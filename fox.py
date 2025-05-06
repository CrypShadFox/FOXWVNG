import imaplib
import email
import os
import sys
import shutil
import mimetypes
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from email.utils import parseaddr

# Banner art
BANNER = r"""
   ╔═══════════════════════════════════════════════════════════════════╗
   ║                                                                   ║
   ║   ███████╗ ██████╗ ██╗  ██╗██╗    ██╗██╗   ██╗███╗   ██╗ ██████╗  ║
   ║   ██╔════╝██╔═══██╗╚██╗██╔╝██║    ██║██║   ██║████╗  ██║██╔════╝  ║
   ║   █████╗  ██║   ██║ ╚███╔╝ ██║ █╗ ██║██║   ██║██╔██╗ ██║██║  ███╗ ║
   ║   ██╔══╝  ██║   ██║ ██╔██╗ ██║███╗██║╚██╗ ██╔╝██║╚██╗██║██║   ██║ ║
   ║   ██║     ╚██████╔╝██╔╝ ██╗╚███╔███╔╝ ╚████╔╝ ██║ ╚████║╚██████╔╝ ║
   ║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝   ╚═══╝  ╚═╝  ╚═══╝ ╚═════╝  ║
   ║                                                                   ║
   ║              Terminal-based Email Explorer v1.0                   ║
   ║                                                                   ║
   ╚═══════════════════════════════════════════════════════════════════╝
"""

# Email configuration
DEFAULT_EMAIL_USER = "example@example.com"
DEFAULT_EMAIL_PASSWORD = "123456"
DEFAULT_IMAP_SERVER = "imap.example.com"
DEFAULT_IMAP_PORT = 993

class EmailBrowser:
    def __init__(self):
        self.mail = None
        self.selected_folder = None
        self.messages = []
        self.current_index = 0
        self.total_messages = 0
        self.folders = []
        
        # Initialize with default settings
        self.email_user = DEFAULT_EMAIL_USER
        self.email_password = DEFAULT_EMAIL_PASSWORD
        self.imap_server = DEFAULT_IMAP_SERVER
        self.imap_port = DEFAULT_IMAP_PORT
        
        # Config file path
        self.config_dir = Path.home() / ".email_browser"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "accounts.txt"
        
        # Load saved accounts
        self.saved_accounts = self.load_saved_accounts()

    def load_saved_accounts(self):
        """Load saved email accounts from config file"""
        accounts = []
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    lines = f.readlines()
                    
                i = 0
                while i < len(lines):
                    if i + 3 < len(lines):  # Need at least 4 lines for a complete account
                        name = lines[i].strip()
                        server = lines[i+1].strip()
                        port = int(lines[i+2].strip())
                        user = lines[i+3].strip()
                        
                        accounts.append({
                            'name': name,
                            'server': server,
                            'port': port,
                            'user': user
                        })
                        
                    i += 5  # Skip the separator line
            except Exception as e:
                print(f"Error loading saved accounts: {str(e)}")
                
        return accounts
        
    def save_account(self, name, server, port, user):
        """Save an account to the config file"""
        try:
            with open(self.config_file, 'a') as f:
                f.write(f"{name}\n")
                f.write(f"{server}\n")
                f.write(f"{port}\n")
                f.write(f"{user}\n")
                f.write("-" * 30 + "\n")
                
            # Reload saved accounts
            self.saved_accounts = self.load_saved_accounts()
            return True
        except Exception as e:
            print(f"Error saving account: {str(e)}")
            return False
            
    def configure_connection(self):
        """Configure email connection settings"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print("\n" + "=" * 80)
        print("📧 EMAIL ACCOUNT CONFIGURATION")
        print("=" * 80)
        
        # Show saved accounts if any
        if self.saved_accounts:
            print("\nSaved accounts:")
            for i, account in enumerate(self.saved_accounts):
                print(f"{i+1}. {account['name']} ({account['user']} @ {account['server']})")
                
            print(f"{len(self.saved_accounts)+1}. Use default settings")
            print(f"{len(self.saved_accounts)+2}. Enter new settings")
            
            try:
                choice = int(input("\nSelect an option: "))
                
                if 1 <= choice <= len(self.saved_accounts):
                    # Use saved account
                    account = self.saved_accounts[choice-1]
                    self.imap_server = account['server']
                    self.imap_port = account['port']
                    self.email_user = account['user']
                    self.email_password = input(f"Enter password for {self.email_user}: ")
                    return True
                elif choice == len(self.saved_accounts)+1:
                    # Use default settings
                    self.imap_server = DEFAULT_IMAP_SERVER
                    self.imap_port = DEFAULT_IMAP_PORT
                    self.email_user = DEFAULT_EMAIL_USER
                    self.email_password = DEFAULT_EMAIL_PASSWORD
                    return True
                elif choice == len(self.saved_accounts)+2:
                    # Enter new settings
                    pass
                else:
                    print("Invalid choice, using default settings")
                    return True
            except ValueError:
                print("Invalid input, using default settings")
                return True
        
        # Enter new settings
        print("\nEnter connection details (press Enter to use default):")
        
        server = input(f"IMAP Server [{DEFAULT_IMAP_SERVER}]: ")
        if server:
            self.imap_server = server
            
        port_str = input(f"IMAP Port [{DEFAULT_IMAP_PORT}]: ")
        if port_str:
            try:
                self.imap_port = int(port_str)
            except ValueError:
                print(f"Invalid port number, using default: {DEFAULT_IMAP_PORT}")
                self.imap_port = DEFAULT_IMAP_PORT
                
        user = input(f"Email Username [{DEFAULT_EMAIL_USER}]: ")
        if user:
            self.email_user = user
            
        password = input("Email Password (leave empty for default): ")
        if password:
            self.email_password = password
        
        # Ask if user wants to save these settings
        save = input("\nSave these settings for future use? (y/n): ").lower()
        if save == 'y':
            name = input("Enter a name for this account: ")
            if name:
                self.save_account(name, self.imap_server, self.imap_port, self.email_user)
                print(f"✅ Account '{name}' saved")
        
        return True

    def connect(self):
        """Connect to the email server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_user, self.email_password)
            print(f"✅ Successfully connected to {self.imap_server} as {self.email_user}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False

    def get_folders(self):
        """Get all available folders/mailboxes"""
        if not self.mail:
            print("Not connected to server")
            return []
            
        status, response = self.mail.list()
        if status != 'OK':
            print("Failed to retrieve folders")
            return []
            
        self.folders = []
        for folder in response:
            folder_name = folder.decode().split('"/"')[-1].strip().strip('"')
            self.folders.append(folder_name)
        return self.folders

    def select_folder(self, folder_name="INBOX"):
        """Select a specific folder/mailbox"""
        if not self.mail:
            print("Not connected to server")
            return False
            
        try:
            status, data = self.mail.select(folder_name)
            if status != 'OK':
                print(f"❌ Failed to select folder '{folder_name}'")
                return False
                
            self.selected_folder = folder_name
            self.total_messages = int(data[0])
            print(f"📁 Selected folder: {folder_name} ({self.total_messages} messages)")
            return True
        except Exception as e:
            print(f"❌ Error selecting folder: {str(e)}")
            return False

    def fetch_message_ids(self, limit=None, criteria="ALL"):
        """Fetch message IDs based on criteria"""
        if not self.mail or not self.selected_folder:
            print("Not connected or no folder selected")
            return []
            
        try:
            status, data = self.mail.search(None, criteria)
            if status != 'OK':
                print("Failed to fetch message IDs")
                return []
                
            # Get all message IDs
            msg_ids = data[0].split()
            
            # Apply limit if specified
            if limit and limit < len(msg_ids):
                msg_ids = msg_ids[-limit:]
                
            return msg_ids
        except Exception as e:
            print(f"Error fetching message IDs: {str(e)}")
            return []

    def get_text_body(self, msg):
        """Extract plain text from email message"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disp = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disp:
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(errors="ignore")
            return "[No plain text content found]"
        else:
            payload = msg.get_payload(decode=True)
            return payload.decode(errors="ignore") if payload else "[Empty body]"
            
    def get_html_content(self, msg):
        """Extract HTML content from email message"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disp = str(part.get("Content-Disposition"))
                
                if content_type == "text/html" and "attachment" not in content_disp:
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(errors="ignore")
            return None
        elif msg.get_content_type() == "text/html":
            payload = msg.get_payload(decode=True)
            return payload.decode(errors="ignore") if payload else None
        return None

    def format_address(self, address):
        """Format email address nicely"""
        if not address:
            return "[No address]"
        return address

    def format_date(self, date_str):
        """Format date string in a consistent way"""
        if not date_str:
            return "[No date]"
        try:
            # This is a simple format - could be improved to handle various date formats
            return date_str
        except:
            return date_str

    def load_messages(self, count=20):
        """Load a specific number of recent messages"""
        if not self.mail or not self.selected_folder:
            print("Not connected or no folder selected")
            return False
            
        msg_ids = self.fetch_message_ids(limit=count)
        if not msg_ids:
            print("No messages found")
            return False
            
        self.messages = []
        self.current_index = 0
        
        print(f"Loading {len(msg_ids)} messages...")
        
        for num in msg_ids:
            try:
                status, msg_data = self.mail.fetch(num, "(RFC822)")
                if status != 'OK':
                    print(f"Failed to fetch message {num}")
                    continue
                    
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decode subject
                subject_header = msg["Subject"]
                if subject_header:
                    subject, encoding = decode_header(subject_header)[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or 'utf-8', errors='ignore')
                else:
                    subject = "[No Subject]"
                
                # Extract message info
                message_info = {
                    'id': num,
                    'subject': subject,
                    'from': self.format_address(msg.get("From")),
                    'to': self.format_address(msg.get("To")),
                    'date': self.format_date(msg.get("Date")),
                    'body': None,  # Load body only when viewing to save memory
                    'raw_message': msg
                }
                
                self.messages.append(message_info)
                
            except Exception as e:
                print(f"Error processing message {num}: {str(e)}")
        
        print(f"✅ Loaded {len(self.messages)} messages")
        return True

    def display_message_list(self):
        """Display a list of loaded messages"""
        if not self.messages:
            print("No messages loaded")
            return
            
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print(f"\n{'=' * 80}")
        print(f"📧 ACCOUNT: {self.email_user} | FOLDER: {self.selected_folder}")
        print(f"📩 Messages: {self.current_index + 1}/{len(self.messages)} displayed, {self.total_messages} total in folder")
        print(f"{'=' * 80}")
        
        start_idx = max(0, self.current_index - 5)
        end_idx = min(len(self.messages), start_idx + 10)
        
        for i in range(start_idx, end_idx):
            msg = self.messages[i]
            prefix = "➤" if i == self.current_index else " "
            date_str = msg['date'][:16] if len(msg['date']) > 16 else msg['date']
            truncated_subject = msg['subject'][:50] + ("..." if len(msg['subject']) > 50 else "")
            print(f"{prefix} {i+1:3d} | {date_str:16} | {msg['from'][:25]:25} | {truncated_subject}")
        
        print(f"{'=' * 80}")
        self.show_navigation_help()
        
    def display_current_message(self):
        """Display the currently selected message in detail"""
        if not self.messages or self.current_index >= len(self.messages):
            print("No message selected")
            return
            
        msg_info = self.messages[self.current_index]
        
        # Lazy load the body if not already loaded
        if msg_info['body'] is None:
            msg_info['body'] = self.get_text_body(msg_info['raw_message'])
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(BANNER)
        print(f"\n{'=' * 80}")
        print(f"MESSAGE {self.current_index + 1}/{len(self.messages)}")
        print(f"{'=' * 80}")
        print(f"Subject: {msg_info['subject']}")
        print(f"From:    {msg_info['from']}")
        print(f"To:      {msg_info['to']}")
        print(f"Date:    {msg_info['date']}")
        print(f"{'=' * 80}")
        print(f"BODY:")
        print(f"{'=' * 80}")
        
        # Display body with line wrapping
        body = msg_info['body']
        width = 80
        for i in range(0, len(body), width):
            print(body[i:i+width])
        
        print(f"\n{'=' * 80}")
        print(f"{'=' * 80}")

    def show_navigation_help(self):
        """Show available navigation commands"""
        print("Commands:")
        print("  n: Next message     p: Previous message    v: View selected message")
        print("  f: Change folder    r: Refresh messages    s: Search messages")
        print("  e: Export message   c: Compose message     a: Change account")
        print("  q: Quit")

    def navigate_next(self):
        """Navigate to next message"""
        if self.current_index < len(self.messages) - 1:
            self.current_index += 1
            return True
        else:
            print("Already at the last message")
            return False

    def navigate_previous(self):
        """Navigate to previous message"""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        else:
            print("Already at the first message")
            return False

    def search_messages(self, search_term):
        """Search for messages containing a specific term"""
        search_criteria = f'TEXT "{search_term}"'
        msg_ids = self.fetch_message_ids(criteria=search_criteria)
        
        if not msg_ids:
            print(f"No messages found matching '{search_term}'")
            return False
            
        print(f"Found {len(msg_ids)} messages matching '{search_term}'")
        self.messages = []
        self.current_index = 0
        
        for num in msg_ids:
            try:
                status, msg_data = self.mail.fetch(num, "(RFC822)")
                if status != 'OK':
                    continue
                    
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decode subject
                subject_header = msg["Subject"]
                if subject_header:
                    subject, encoding = decode_header(subject_header)[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or 'utf-8', errors='ignore')
                else:
                    subject = "[No Subject]"
                
                # Extract message info
                message_info = {
                    'id': num,
                    'subject': subject,
                    'from': self.format_address(msg.get("From")),
                    'to': self.format_address(msg.get("To")),
                    'date': self.format_date(msg.get("Date")),
                    'body': None,
                    'raw_message': msg
                }
                
                self.messages.append(message_info)
                
            except Exception as e:
                print(f"Error processing message: {str(e)}")
        
        return True

    def select_folder_interactive(self):
        """Let user select a folder interactively"""
        folders = self.get_folders()
        
        if not folders:
            print("No folders available")
            return False
            
        print("\nAvailable folders:")
        for i, folder in enumerate(folders):
            print(f"{i+1}. {folder}")
            
        try:
            choice = int(input("\nSelect folder number: ")) - 1
            if 0 <= choice < len(folders):
                return self.select_folder(folders[choice])
            else:
                print("Invalid folder selection")
                return False
        except ValueError:
            print("Please enter a number")
            return False

    def disconnect(self):
        """Disconnect from the email server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                print("Disconnected from the server")
            except:
                pass

    def export_message(self):
        """Export the current message to file(s)"""
        if not self.messages or self.current_index >= len(self.messages):
            print("No message selected to export")
            return
            
        msg_info = self.messages[self.current_index]
        raw_msg = msg_info['raw_message']
        
        # Lazy load the body if not already loaded
        if msg_info['body'] is None:
            msg_info['body'] = self.get_text_body(raw_msg)
        
        # Create an export directory if it doesn't exist
        export_dir = Path("exported_emails")
        export_dir.mkdir(exist_ok=True)
        
        # Create a sanitized filename based on the subject
        subject = msg_info['subject']
        sanitized_subject = "".join(c for c in subject if c.isalnum() or c in " ._-").strip()
        if not sanitized_subject:
            sanitized_subject = "no_subject"
        
        # Add date info to filename
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{date_str}_{sanitized_subject[:30]}"
        
        print("\nExport options:")
        print("1. Text file (.txt)")
        print("2. HTML file (.html)")
        print("3. Full email with attachments (.eml)")
        print("4. All formats")
        
        try:
            export_choice = input("\nSelect export format (1-4): ")
            
            # Create a subdirectory for this email if exporting attachments
            if export_choice in ['3', '4']:
                email_dir = export_dir / base_filename
                email_dir.mkdir(exist_ok=True)
            
            # Export as text
            if export_choice in ['1', '4']:
                self.export_as_text(export_dir, base_filename, msg_info)
                
            # Export as HTML
            if export_choice in ['2', '4']:
                self.export_as_html(export_dir, base_filename, raw_msg)
                
            # Export as EML with attachments
            if export_choice in ['3', '4']:
                self.export_as_eml(export_dir, base_filename, raw_msg)
                
            print(f"\n✅ Export completed to {export_dir}")
            
        except Exception as e:
            print(f"❌ Error during export: {str(e)}")
    
    def export_as_text(self, export_dir, base_filename, msg_info):
        """Export message as plain text"""
        txt_path = export_dir / f"{base_filename}.txt"
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {msg_info['subject']}\n")
            f.write(f"From: {msg_info['from']}\n")
            f.write(f"To: {msg_info['to']}\n")
            f.write(f"Date: {msg_info['date']}\n")
            f.write(f"{'-' * 50}\n\n")
            f.write(msg_info['body'])
            
        print(f"📄 Exported as text: {txt_path}")
    
    def export_as_html(self, export_dir, base_filename, raw_msg):
        """Export message as HTML if available"""
        html_content = self.get_html_content(raw_msg)
        
        if html_content:
            html_path = export_dir / f"{base_filename}.html"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"🌐 Exported as HTML: {html_path}")
        else:
            print("❌ No HTML content available for this message")
    
    def export_as_eml(self, export_dir, base_filename, raw_msg):
        """Export as EML file with attachments"""
        # Save the raw email
        eml_path = export_dir / f"{base_filename}.eml"
        
        with open(eml_path, 'wb') as f:
            # Get the raw bytes
            if hasattr(raw_msg, '_payload'):
                f.write(raw_msg.as_bytes())
            else:
                # Fallback if we don't have the original bytes
                f.write(raw_msg.as_string().encode('utf-8'))
                
        print(f"📧 Exported as EML: {eml_path}")
        
        # Extract attachments
        attachments_dir = export_dir / base_filename / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        
        attachment_count = 0
        
        for part in raw_msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            filename = part.get_filename()
            if not filename:
                # Skip non-attachments (like inline images)
                content_id = part.get('Content-ID')
                if content_id:
                    # This is likely an inline image
                    extension = mimetypes.guess_extension(part.get_content_type())
                    if extension:
                        filename = f"inline_image_{attachment_count}{extension}"
                    else:
                        filename = f"inline_content_{attachment_count}"
                else:
                    continue
                    
            # Clean filename
            clean_filename = "".join(c for c in filename if c not in '\\/:*?"<>|')
            if not clean_filename:
                clean_filename = f"attachment_{attachment_count}"
                
            file_path = attachments_dir / clean_filename
            
            # Save the attachment
            with open(file_path, 'wb') as f:
                f.write(part.get_payload(decode=True))
                
            attachment_count += 1
            
        if attachment_count > 0:
            print(f"📎 Extracted {attachment_count} attachments to {attachments_dir}")
        else:
            print("ℹ️ No attachments found")

    def run(self):
        """Main application loop"""
        # Configure connection settings first
        if not self.configure_connection():
            print("Configuration cancelled")
            return
            
        # Connect with configured settings
        if not self.connect():
            return
            
        # Default to Sent folder
        if not self.select_folder("Sent"):
            if not self.select_folder("INBOX"):  # Fallback to inbox
                print("Could not select any folder")
                self.disconnect()
                return
                
        # Load initial messages
        self.load_messages(20)
        
        # Show the message list
        self.display_message_list()
        
        # Main interaction loop
        while True:
            choice = input("\nEnter command (h for help): ").lower()
            
            if choice == 'q':
                break
            elif choice == 'h':
                self.show_navigation_help()
            elif choice == 'n':
                if self.navigate_next():
                    self.display_message_list()
            elif choice == 'p':
                if self.navigate_previous():
                    self.display_message_list()
            elif choice == 'v':
                self.display_current_message()
                input("Press Enter to continue...")
                self.display_message_list()
            elif choice == 'l':
                self.display_message_list()
            elif choice == 'r':
                self.load_messages(20)
                self.display_message_list()
            elif choice == 'f':
                if self.select_folder_interactive():
                    self.load_messages(20)
                    self.display_message_list()
            elif choice == 's':
                search_term = input("Enter search term: ")
                if search_term and self.search_messages(search_term):
                    self.display_message_list()
            elif choice == 'e':
                self.export_message()
                input("Press Enter to continue...")
                self.display_message_list()
            elif choice == 'c':
                print("Compose feature not implemented yet")
            elif choice == 'a':
                print("\nChanging email account...")
                self.disconnect()
                if self.configure_connection() and self.connect():
                    if not self.select_folder("Sent"):
                        self.select_folder("INBOX")
                    self.load_messages(20)
                    self.display_message_list()
                else:
                    print("Failed to connect with new settings. Exiting...")
                    break
            else:
                print("Unknown command. Type 'h' for help.")
                
        # Disconnect when done
        self.disconnect()


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    print("\nWelcome to FoxWVNG - The Terminal-based Email Explorer!")
    print("Starting up...")
    
    browser = EmailBrowser()
    browser.run()
