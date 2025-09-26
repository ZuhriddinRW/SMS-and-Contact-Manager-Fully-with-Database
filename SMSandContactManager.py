import re
import psycopg2
from datetime import datetime


class Contact :
    def __init__(self, name, phone, email="") :
        self.__name = name.strip ()
        self.__phone = self.__format_phone ( phone )
        self.__email = email.strip ()
        self.__created_at = datetime.now ().strftime ( "%Y-%m-%d %H:%M" )
        self.__sms_count = 0

    def __format_phone(self, phone) :
        clean_phone = re.sub ( r'[^\d+]', '', phone )

        uz_pattern = r'^(90|91|93|94|95|97|98|99|88|50|33|77|71|78)[0-9]{7}$'

        if re.match ( uz_pattern, clean_phone ) :
            return '+998' + clean_phone

        if clean_phone.startswith ( '+' ) :
            return clean_phone

        return clean_phone

    def __is_valid_phone(self, phone) :
        digits_only = re.sub ( r'[^\d]', '', phone )
        return len ( digits_only ) >= 7

    def get_name(self) :
        return self.__name

    def get_phone(self) :
        return self.__phone

    def get_email(self) :
        return self.__email

    def get_created_at(self) :
        return self.__created_at

    def get_sms_count(self) :
        return self.__sms_count

    def set_name(self, name) :
        if name and name.strip () :
            self.__name = name.strip ()
        else :
            raise ValueError ( "Name cannot be empty" )

    def set_phone(self, phone) :
        if self.__is_valid_phone ( phone ) :
            self.__phone = self.__format_phone ( phone )
        else :
            raise ValueError ( "Invalid phone number" )

    def set_email(self, email) :
        self.__email = email.strip ()

    def increment_sms_count(self) :
        self.__sms_count += 1

    def is_phone_valid(self) :
        return self.__is_valid_phone ( self.__phone )

    def __str__(self) :
        if self.__email :
            return f"{self.__name} | {self.__phone} | {self.__email} | SMS: {self.__sms_count}"
        return f"{self.__name} | {self.__phone} | SMS: {self.__sms_count}"


class SMS :
    def __init__(self, to_phone, message, contact_name="Unknown") :
        self.__to_phone = to_phone
        self.__message = message
        self.__contact_name = contact_name
        self.__sent_at = datetime.now ().strftime ( "%Y-%m-%d %H:%M:%S" )
        self.__status = "Sent"

    def get_to_phone(self) :
        return self.__to_phone

    def get_message(self) :
        return self.__message

    def get_contact_name(self) :
        return self.__contact_name

    def get_sent_at(self) :
        return self.__sent_at

    def get_status(self) :
        return self.__status

    def set_status(self, status) :
        self.__status = status

    def __str__(self) :
        return f"To: {self.__contact_name} ({self.__to_phone})\nTime: {self.__sent_at}\nMessage: {self.__message}\nStatus: {self.__status}\n"


class ContactManager :
    def __init__(self) :
        self.__contacts = []
        try :
            self.conn = psycopg2.connect (
                dbname="Contact And SMS Manager Full",
                user="postgres",
                password="uniquepincode2026",
                host="localhost"
            )
            self.cur = self.conn.cursor ()
            self.__create_tables ()
            self.__load_contacts ()
        except :
            print ( "Database not connected, using memory only" )
            self.conn = None
            self.cur = None

    def __create_tables(self) :
        if not self.conn :
            return
        try :
            self.cur.execute ( '''
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    phone VARCHAR(20) UNIQUE,
                    email VARCHAR(100),
                    sms_count INTEGER DEFAULT 0
                )
            ''' )

            self.cur.execute ( '''
                CREATE TABLE IF NOT EXISTS sms_history (
                    id SERIAL PRIMARY KEY,
                    to_phone VARCHAR(20),
                    message TEXT,
                    contact_name VARCHAR(100),
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''' )
            self.conn.commit ()
        except :
            pass

    def __load_contacts(self) :
        if not self.conn :
            return
        try :
            self.cur.execute ( "SELECT name, phone, email, sms_count FROM contacts" )
            for row in self.cur.fetchall () :
                contact = Contact ( row[0], row[1], row[2] )
                contact._Contact__sms_count = row[3]
                self.__contacts.append ( contact )
        except :
            pass

    def __save_contact_to_db(self, contact) :
        if not self.conn :
            return
        try :
            self.cur.execute (
                "INSERT INTO contacts (name, phone, email, sms_count) VALUES (%s, %s, %s, %s)",
                (contact.get_name (), contact.get_phone (), contact.get_email (), contact.get_sms_count ())
            )
            self.conn.commit ()
        except :
            pass

    def __update_contact_in_db(self, contact) :
        if not self.conn :
            return
        try :
            self.cur.execute (
                "UPDATE contacts SET name=%s, email=%s, sms_count=%s WHERE phone=%s",
                (contact.get_name (), contact.get_email (), contact.get_sms_count (), contact.get_phone ())
            )
            self.conn.commit ()
        except :
            pass

    def __delete_contact_from_db(self, phone) :
        if not self.conn :
            return
        try :
            self.cur.execute ( "DELETE FROM contacts WHERE phone=%s", (phone,) )
            self.conn.commit ()
        except :
            pass

    def __is_valid_phone(self, phone) :
        clean_phone = re.sub ( r'[^\d+]', '', phone )
        return len ( clean_phone ) >= 7 and re.match ( r'^[\+]?[0-9]+$', clean_phone )

    def __is_duplicate_contact(self, phone) :
        for contact in self.__contacts :
            if contact.get_phone () == phone :
                return True
        return False

    def get_contacts_count(self) :
        return len ( self.__contacts )

    def get_all_contacts(self) :
        return self.__contacts.copy ()

    def add_contact(self) :
        print ( "\nAdd New Contact" )
        print ( "-" * 30 )

        name = input ( "Name: " ).strip ()
        if not name :
            print ( "Name cannot be empty!" )
            return False

        phone = input ( "Phone: " ).strip ()
        if not self.__is_valid_phone ( phone ) :
            print ( "Invalid phone number!" )
            return False

        temp_contact = Contact ( "temp", phone )
        if self.__is_duplicate_contact ( temp_contact.get_phone () ) :
            print ( "Contact with this phone number already exists!" )
            return False

        email = input ( "Email (optional): " ).strip ()

        try :
            contact = Contact ( name, phone, email )
            self.__contacts.append ( contact )
            self.__save_contact_to_db ( contact )
            print ( f"Contact '{name}' added successfully!" )
            return True
        except Exception as e :
            print ( f"Error adding contact: {e}" )
            return False

    def view_contacts(self) :
        if not self.__contacts :
            print ( "No contacts found!" )
            return

        print ( f"\nAll Contacts ({len ( self.__contacts )} total)" )
        print ( "-" * 50 )
        for i, contact in enumerate ( self.__contacts, 1 ) :
            print ( f"{i}. {contact}" )
        print ( "-" * 50 )

    def search_contacts(self) :
        if not self.__contacts :
            print ( "No contacts to search!" )
            return

        search_term = input ( "\nSearch by name or phone: " ).strip ().lower ()
        if not search_term :
            return

        found_contacts = []
        for i, contact in enumerate ( self.__contacts ) :
            if search_term in contact.get_name ().lower () or search_term in contact.get_phone () :
                found_contacts.append ( (i, contact) )

        if found_contacts :
            print ( f"\nFound {len ( found_contacts )} contact(s):" )
            print ( "-" * 50 )
            for i, contact in found_contacts :
                print ( f"{i + 1}. {contact}" )
        else :
            print ( "No contacts found!" )

    def delete_contact(self) :
        if not self.__contacts :
            print ( "No contacts to delete!" )
            return

        self.view_contacts ()
        try :
            choice = int ( input ( "\nEnter contact number to delete: " ) ) - 1
            if 0 <= choice < len ( self.__contacts ) :
                contact = self.__contacts[choice]
                confirm = input ( f"Delete '{contact.get_name ()}'? (y/n): " ).lower ()
                if confirm == 'y' :
                    self.__delete_contact_from_db ( contact.get_phone () )
                    deleted_contact = self.__contacts.pop ( choice )
                    print ( f"Contact '{deleted_contact.get_name ()}' deleted!" )
                    return True
                else :
                    print ( "Delete cancelled!" )
            else :
                print ( "Invalid choice!" )
        except ValueError :
            print ( "Please enter a valid number!" )
        return False

    def edit_contact(self) :
        if not self.__contacts :
            print ( "No contacts to edit!" )
            return

        self.view_contacts ()
        try :
            choice = int ( input ( "\nEnter contact number to edit: " ) ) - 1
            if 0 <= choice < len ( self.__contacts ) :
                contact = self.__contacts[choice]
                print ( f"\nEditing: {contact.get_name ()}" )

                new_name = input ( f"New name (current: {contact.get_name ()}): " ).strip ()
                if new_name :
                    contact.set_name ( new_name )

                new_phone = input ( f"New phone (current: {contact.get_phone ()}): " ).strip ()
                if new_phone :
                    contact.set_phone ( new_phone )

                new_email = input ( f"New email (current: {contact.get_email ()}): " ).strip ()
                contact.set_email ( new_email )

                self.__update_contact_in_db ( contact )
                print ( "Contact updated successfully!" )
                return True
            else :
                print ( "Invalid choice!" )
        except ValueError :
            print ( "Please enter a valid number!" )
        except Exception as e :
            print ( f"Error: {e}" )
        return False

    def find_contact_by_phone(self, phone) :
        for contact in self.__contacts :
            if contact.get_phone () == phone :
                return contact
        return None

    def clear_all_contacts(self) :
        if not self.__contacts :
            print ( "No contacts to clear!" )
            return False

        confirm = input ( f"Delete all {len ( self.__contacts )} contacts? (y/n): " ).lower ()
        if confirm == 'y' :
            if self.conn :
                try :
                    self.cur.execute ( "DELETE FROM contacts" )
                    self.conn.commit ()
                except :
                    pass
            self.__contacts.clear ()
            print ( "All contacts cleared!" )
            return True
        else :
            print ( "Clear cancelled!" )
            return False


class SMSManager :
    def __init__(self, contact_manager) :
        self.__contact_manager = contact_manager
        self.__sms_history = []
        self.__load_sms_history ()

    def __load_sms_history(self) :
        if not self.__contact_manager.conn :
            return
        try :
            self.__contact_manager.cur.execute (
                "SELECT to_phone, message, contact_name, sent_at FROM sms_history ORDER BY sent_at" )
            for row in self.__contact_manager.cur.fetchall () :
                sms = SMS ( row[0], row[1], row[2] )
                sms._SMS__sent_at = row[3].strftime ( "%Y-%m-%d %H:%M:%S" )
                self.__sms_history.append ( sms )
        except :
            pass

    def __save_sms_to_db(self, sms) :
        if not self.__contact_manager.conn :
            return
        try :
            self.__contact_manager.cur.execute (
                "INSERT INTO sms_history (to_phone, message, contact_name) VALUES (%s, %s, %s)",
                (sms.get_to_phone (), sms.get_message (), sms.get_contact_name ())
            )
            self.__contact_manager.conn.commit ()
        except :
            pass

    def get_sms_count(self) :
        return len ( self.__sms_history )

    def get_sms_history(self) :
        return self.__sms_history.copy ()

    def send_sms_to_contact(self) :
        contacts = self.__contact_manager.get_all_contacts ()
        if not contacts :
            print ( "No contacts found!" )
            return False

        print ( "\nSend SMS to Contact" )
        self.__contact_manager.view_contacts ()

        try :
            choice = int ( input ( "Choose contact number: " ) ) - 1
            if 0 <= choice < len ( contacts ) :
                contact = contacts[choice]
                message = input ( "Enter message: " ).strip ()

                if message :
                    sms = SMS ( contact.get_phone (), message, contact.get_name () )
                    self.__sms_history.append ( sms )
                    self.__save_sms_to_db ( sms )
                    contact.increment_sms_count ()
                    self.__contact_manager._ContactManager__update_contact_in_db ( contact )
                    print ( f"SMS sent to {contact.get_name ()}!" )
                    return True
                else :
                    print ( "Message cannot be empty!" )
            else :
                print ( "Invalid choice!" )
        except ValueError :
            print ( "Please enter a valid number!" )
        return False

    def send_sms_to_number(self) :
        print ( "\nSend SMS to Number" )
        phone = input ( "Enter phone number: " ).strip ()

        clean_phone = re.sub ( r'[^\d+]', '', phone )
        if len ( clean_phone ) < 7 :
            print ( "Invalid phone number!" )
            return False

        message = input ( "Enter message: " ).strip ()
        if not message :
            print ( "Message cannot be empty!" )
            return False

        try :
            temp_contact = Contact ( "temp", phone )
            formatted_phone = temp_contact.get_phone ()

            existing_contact = self.__contact_manager.find_contact_by_phone ( formatted_phone )
            contact_name = existing_contact.get_name () if existing_contact else "Unknown"

            sms = SMS ( formatted_phone, message, contact_name )
            self.__sms_history.append ( sms )
            self.__save_sms_to_db ( sms )

            if existing_contact :
                existing_contact.increment_sms_count ()
                self.__contact_manager._ContactManager__update_contact_in_db ( existing_contact )

            print ( f"SMS sent to {formatted_phone}!" )
            return True
        except Exception as e :
            print ( f"Error: {e}" )
            return False

    def view_sms_history(self) :
        if not self.__sms_history :
            print ( "No SMS history!" )
            return

        print ( f"\nSMS History ({len ( self.__sms_history )} messages)" )
        print ( "-" * 50 )
        for i, sms in enumerate ( self.__sms_history, 1 ) :
            print ( f"{i}. {sms}" )
            print ( "-" * 30 )

    def view_sms_statistics(self) :
        if not self.__sms_history :
            print ( "No SMS statistics available!" )
            return

        total_sms = len ( self.__sms_history )
        today = datetime.now ().strftime ( "%Y-%m-%d" )
        today_sms = sum ( 1 for sms in self.__sms_history if sms.get_sent_at ().startswith ( today ) )

        print ( "\nSMS Statistics" )
        print ( "-" * 30 )
        print ( f"Total SMS sent: {total_sms}" )
        print ( f"SMS sent today: {today_sms}" )
        print ( "Most active contacts:" )

        contact_stats = {}
        for sms in self.__sms_history :
            name = sms.get_contact_name ()
            contact_stats[name] = contact_stats.get ( name, 0 ) + 1

        sorted_contacts = sorted ( contact_stats.items (), key=lambda x : x[1], reverse=True )[:5]
        for name, count in sorted_contacts :
            print ( f"  {name}: {count} SMS" )

    def clear_sms_history(self) :
        if not self.__sms_history :
            print ( "No SMS history to clear!" )
            return False

        confirm = input ( f"Delete all {len ( self.__sms_history )} SMS records? (y/n): " ).lower ()
        if confirm == 'y' :
            if self.__contact_manager.conn :
                try :
                    self.__contact_manager.cur.execute ( "DELETE FROM sms_history" )
                    self.__contact_manager.cur.execute ( "UPDATE contacts SET sms_count = 0" )
                    self.__contact_manager.conn.commit ()
                except :
                    pass

            for contact in self.__contact_manager.get_all_contacts () :
                contact._Contact__sms_count = 0

            self.__sms_history.clear ()
            print ( "SMS history cleared!" )
            return True
        else :
            print ( "Clear cancelled!" )
            return False


def main() :
    contact_manager = ContactManager ()
    sms_manager = SMSManager ( contact_manager )

    while True :
        print ( "\n" + "=" * 40 )
        print ( "    CONTACT & SMS MANAGER" )
        print ( "=" * 40 )
        print ( "CONTACTS:" )
        print ( "1. View all contacts" )
        print ( "2. Add new contact" )
        print ( "3. Search contacts" )
        print ( "4. Edit contact" )
        print ( "5. Delete contact" )
        print ( "\nSMS:" )
        print ( "6. Send SMS to contact" )
        print ( "7. Send SMS to number" )
        print ( "8. View SMS history" )
        print ( "9. SMS statistics" )
        print ( "\nCLEAR DATA:" )
        print ( "10. Clear all contacts" )
        print ( "11. Clear SMS history" )
        print ( "12. Clear everything" )
        print ( "\n0. Exit" )
        print ( "=" * 40 )

        choice = input ( "Choose option: " ).strip ()

        match choice :
            case "1" :
                contact_manager.view_contacts ()
            case "2" :
                contact_manager.add_contact ()
            case "3" :
                contact_manager.search_contacts ()
            case "4" :
                contact_manager.edit_contact ()
            case "5" :
                contact_manager.delete_contact ()
            case "6" :
                sms_manager.send_sms_to_contact ()
            case "7" :
                sms_manager.send_sms_to_number ()
            case "8" :
                sms_manager.view_sms_history ()
            case "9" :
                sms_manager.view_sms_statistics ()
            case "10" :
                contact_manager.clear_all_contacts ()
            case "11" :
                sms_manager.clear_sms_history ()
            case "12" :
                contact_manager.clear_all_contacts ()
                sms_manager.clear_sms_history ()
                print ( "All data cleared!" )
            case "0" :
                print ( "Goodbye!" )
                break
            case _ :
                print ( "Invalid choice! Please try again." )


if __name__ == "__main__" :
    main ()