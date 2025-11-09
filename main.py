from collections import UserDict
import re
from datetime import datetime, timedelta
import pickle


class Field:
    """
    Base class for record fields in the address book.
    Stores a single value and provides string representation.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """
    Represents a contact's name.
    The name field is required and cannot be empty.
    """

    def __init__(self, value):
        if not value:
            raise ValueError("Name can't be empty")
        super().__init__(value)


class Phone(Field):
    """
    Represents a contact's phone number.
    Validates that the phone number consists of exactly 10 digits.
    """

    def __init__(self, phone):
        if not re.fullmatch(r"\d{10}", phone):
            raise ValueError("The phone should contain 10 digits")
        super().__init__(phone)


class Birthday(Field):
    """
    Represents a contact's birthday.
    Validates that the date is in DD.MM.YYYY format.
    """

    def __init__(self, value):
        try:
            date_value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(date_value)


class Record:
    """
    Stores information about a contact:
    name, list of phone numbers, and birthday.
    Provides methods to add, edit, remove phone numbers and add birthday.
    """

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        new_phone = Phone(phone)
        self.phones.append(new_phone)

    def remove_phone(self, phone):
        current_phone = self.find_phone(phone)
        if current_phone is None:
            raise ValueError("Phone not found")
        self.phones.remove(current_phone)

    def edit_phone(self, old_phone, new_phone):
        current_phone = self.find_phone(old_phone)
        if current_phone is None:
            raise ValueError("Phone not found")
        validated_phone = Phone(new_phone)
        current_phone.value = validated_phone.value

    def find_phone(self, phone):
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None

    def add_birthday(self, birthday_string):
        self.birthday = Birthday(birthday_string)

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones)
        birthday_str = (
            self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "No birthday"
        )
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {birthday_str}"

    def __repr__(self):
        return self.__str__()


class AddressBook(UserDict):
    """
    Manages a collection of contact records.
    Provides methods to add, find, delete records and get upcoming birthdays.
    """

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        record = self.find(name)
        if record is None:
            raise KeyError("Record not found")
        del self.data[name]

    def get_upcoming_birthdays(self):
        today_date = datetime.today().date()
        current_year = today_date.year
        result = []

        for record in self.data.values():
            contact_birthday = record.birthday
            if contact_birthday is None:
                continue

            birthday_date = contact_birthday.value.date()
            current_year_birthday_date = birthday_date.replace(year=current_year)

            if current_year_birthday_date < today_date:
                current_year_birthday_date = current_year_birthday_date.replace(
                    year=current_year + 1
                )

            days_diff = (current_year_birthday_date - today_date).days

            if 0 <= days_diff <= 7:
                congratulation_date = current_year_birthday_date
                # If birthday falls on Saturday, move to next Monday
                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                # If birthday falls on Sunday, move to next Monday
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                formatted_congratulation_date = congratulation_date.strftime("%d.%m.%Y")

                result.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": formatted_congratulation_date,
                    }
                )

        return result

    def __str__(self):
        return "\n".join(str(contact) for contact in self.data.values())


def input_error(func):
    """
    Decorator for handling input errors and displaying informative messages.
    Now also handles AttributeError for missing contacts.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError:
            return "Error: Contact not found"
        except (KeyError, ValueError, IndexError) as e:
            return f"Error: {str(e)}"
    return wrapper


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Usage: add [name] [phone]")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Usage: change [name] [old_phone] [new_phone]")
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phones(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Usage: phone [name]")
    name, *_ = args
    record = book.find(name)
    if not record.phones:
        return "No phones found."
    return "; ".join([p.value for p in record.phones])


@input_error
def show_all(_, book: AddressBook):
    if not book.data:
        return "No contacts in address book."
    result = []
    for record in book.data.values():
        phones = "; ".join([p.value for p in record.phones])
        birthday = (
            record.birthday.value.strftime("%d.%m.%Y")
            if record.birthday
            else "No birthday"
        )
        result.append(f"{record.name.value}: {phones}; Birthday: {birthday}")
    return "\n".join(result)


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Usage: add-birthday [name] [DD.MM.YYYY]")
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Usage: show-birthday [name]")
    name, *_ = args
    record = book.find(name)
    if not record.birthday:
        return "No birthday set."
    return record.birthday.value.strftime("%d.%m.%Y")


@input_error
def birthdays(_, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    result = []
    for item in upcoming:
        result.append(f"{item['name']}: {item['congratulation_date']}")
    return "\n".join(result)


@input_error
def parse_input(user_input):
    """
    Parses the user's input command.
    Returns the command and a list of arguments.
    """
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    """
    Main loop of the assistant bot.
    Accepts commands and calls the corresponding handler functions.
    """
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        match command:
            case "close" | "exit":
                save_data(book)
                print("Good bye!")
                break

            case "hello":
                print("How can I help you?")

            case "add":
                print(add_contact(args, book))

            case "change":
                print(change_contact(args, book))

            case "phone":
                print(show_phones(args, book))

            case "all":
                print(show_all(args, book))

            case "add-birthday":
                print(add_birthday(args, book))

            case "show-birthday":
                print(show_birthday(args, book))

            case "birthdays":
                print(birthdays(args, book))

            case _:
                print("Invalid command.")


if __name__ == "__main__":
    main()
