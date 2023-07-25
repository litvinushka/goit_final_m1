from collections import UserDict
from datetime import datetime
import requests
import pickle

#server_address = "http://127.0.0.1:5000"


class Field:
    def __init__(self, value=None):
        self._value = value

    def __str__(self):
        return str(self._value)

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        self._value = value
        self._validate()

    def _validate(self):
        pass


class Name(Field):
    pass


class Phone(Field):
    def _validate(self):
        if self._value is not None and not self._value.isdigit():
            raise ValueError("Неправильный формат номера телефона")


class Birthday(Field):
    def _validate(self):
        if self._value is not None:
            try:
                datetime.strptime(self._value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Неправильный формат дня рождения")


class Record:
    def __init__(self, name, phones=None, birthday=None):
        self.name = name
        self.phones = phones if phones is not None else []
        self.birthday = birthday

    def add_phone(self, phone):
        self.phones.append(phone)

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p._value != phone]

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p._value == old_phone:
                p._value = new_phone

    def days_to_birthday(self):
        if self.birthday is not None:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            next_birthday = datetime.strptime(self.birthday._value, "%Y-%m-%d").replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            return (next_birthday - today).days
        
    def change_phone(self, old_phone, new_phone):
        found_phone = None
        for phone in self.phones:
            if phone._value == old_phone:
                found_phone = phone
                break

        if found_phone:
            found_phone._value = new_phone
            print("Номер телефона успешно изменен.")
        else:
            print("Старый номер телефона не найден.")


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name] = record

    def iterator(self, batch_size=10):
        records = list(self.data.values())
        total_records = len(records)
        current_index = 0

        while current_index < total_records:
            batch = records[current_index: current_index + batch_size]
            current_index += batch_size
            yield batch

    def save_to_file(self, filename):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def load_from_file(self, filename):
        try:
            with open(filename, "rb") as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            # Если файл не найден, оставим книгу пустой
            self.data = {}


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Контакт не найден"
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Неправильный формат ввода"

    return inner


@input_error
def add_contact(name, phone, birthday=None):
    record = Record(Name(name), birthday=Birthday(birthday))
    record.add_phone(Phone(phone))
    address_book.add_record(record)
    return "Контакт добавлен"


@input_error
def change_phone(name, new_phone):
    for record in address_book.data.values():
        if str(record.name).lower() == name.lower():
            old_phone = None
            for phone in record.phones:
                if phone._value == new_phone:
                    raise ValueError("Номер телефона уже существует")
                if old_phone is None:
                    old_phone = phone._value

            if old_phone:
                record.edit_phone(old_phone, new_phone)
                return "Номер телефона изменен"
    raise KeyError("Контакт не найден")


@input_error
def get_phone(name):
    for record in address_book.data.values():
        if str(record.name).lower() == name.lower():
            phones = ', '.join([p._value for p in record.phones])
            return phones
    raise KeyError("Контакт не найден")

@input_error
def get_birthday(name):
    for record in address_book.data.values():
        if record.name._value.lower() == name.lower():
            if record.birthday:
                return record.birthday._value
            else:
                return "День рождения не указан"
    raise KeyError("Контакт не найден")


def search_contacts(query):
    contacts = []
    for record in address_book.data.values():
        if query.lower() in str(record.name).lower():
            contacts.append(record)
        else:
            for phone in record.phones:
                if query in phone._value:
                    contacts.append(record)
                    break
    return contacts


def show_all_contacts():
    contacts = []
    for record in address_book.data.values():
        contact_info = f"{record.name}: {', '.join([p._value for p in record.phones])}"
        if record.birthday:
            contact_info += f", День рождения: {record.birthday._value}"
        contacts.append(contact_info)
    return contacts


#def send_request(command, data):
    url = f"{server_address}/{command}"
    response = requests.post(url, json=data)
    return response.text


def parse_command(command):
    if command == "hello":
        print("Чем я могу помочь?")

    elif command.startswith("add"):
        _, *args = command.split(maxsplit=3)
        if len(args) < 2:
            print("Задайте данные контакта")
        else:
            name, phone, *birthday = args
            birthday = birthday[0] if birthday else None
            print(add_contact(name, phone, birthday))

    elif command.startswith("change"):
        _, *args = command.split(maxsplit=3)
        if len(args) < 2:
            print("Задайте данные контакта")
        else:
            name, new_phone = args
            print(change_phone(name, new_phone))

    elif command.startswith("phone"):
        _, name = command.split(maxsplit=1)
        if not name:
            print("Задайте данные контакта")
        else:
            print(get_phone(name))

    elif command.startswith("birthday"):
        _, name = command.split(maxsplit=1)
        if not name:
            print("Задайте данные контакта")
        else:
            print(get_birthday(name))

    elif command == "show all":
        contacts = show_all_contacts()
        for contact in contacts:
            print(contact)

    elif command in ["good bye", "close", "exit"]:
        print("До свидания!")
        return True


    elif command.startswith("search"):
        _, query = command.split(maxsplit=1)
        if not query:
            print("Задайте строку поиска")
        else:
            results = search_contacts(query)
            if results:
                for record in results:
                    contact_info = f"{record.name}: {', '.join([p._value for p in record.phones])}"
                    if record.birthday:
                        contact_info += f", День рождения: {record.birthday._value}"
                    print(contact_info)
            else:
                print("Контакт не найден")
    else:
        print("Неизвестная команда!")

    return False


def main():
    address_book.load_from_file("address_book.dat")
    print("Доступные команды:\n hello\n add (имя) (номер телефона) (ГГГГ-ММ-ДД)\n birthday (имя)\n change (имя) (номер телефона)\n phone (имя)\n show all\n search (строка поиска)\n good bye/close/exit\n")
    while True:
        command = input("Введите команду: ").lower()

        if parse_command(command):
            break

    # По завершению работы программы, сохраняем данные на диск
    address_book.save_to_file("address_book.dat")


if __name__ == "__main__":
    address_book = AddressBook()
    main()



