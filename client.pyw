import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QFormLayout, QDialog, QPushButton
from PyQt5.QtGui import QFont

def receive_messages(irc, text_edit, thread_running, channel):
    while thread_running():
        try:
            response = irc.recv(2048).decode("UTF-8")
            print(response)  # Debugging purposes
            if response.startswith("PING"):
                irc.send(bytes(f"PONG :{response.split(':')[1]}\n", "UTF-8"))
            elif " 001 " in response:
                irc.send(bytes(f"JOIN {channel}\n", "UTF-8"))
            else:
                text_edit.append(response.split(' :')[-1].strip())
        except socket.error:
            text_edit.append("Connection error. Please restart the client.")
            break

class ServerDetailsDialog(QDialog):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()

        self.server_input = QLineEdit("irc.rizon.net")
        self.channel_input = QLineEdit("#ct")
        self.nick_input = QLineEdit("techchat")

        layout.addRow('Server:', self.server_input)
        layout.addRow('Channel:', self.channel_input)
        layout.addRow('Nickname:', self.nick_input)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

def get_server_details():
    dialog = ServerDetailsDialog()
    result = dialog.exec_()

    if result == QDialog.Accepted:
        return dialog.server_input.text(), dialog.channel_input.text(), dialog.nick_input.text()
    else:
        sys.exit()

class IRCClient(QWidget):
    def __init__(self, irc, thread_running, channel):
        super().__init__()
        self.irc = irc
        self.thread_running = thread_running
        self.channel = channel

        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_input = QLineEdit()

        layout.addWidget(self.text_edit)
        layout.addWidget(self.text_input)

        self.text_input.returnPressed.connect(self.send_message)

        self.setLayout(layout)
        self.setWindowTitle('IRC Client')
        self.resize(800, 600)

        font = QFont("Arial", 14)
        self.text_edit.setFont(font)

    def send_message(self):
        message = self.text_input.text()
        self.text_input.clear()
        if message.startswith("/join "):
            self.channel = message[6:]
            self.irc.send(bytes(f"JOIN {self.channel}\n", "UTF-8"))
        elif message.startswith("/msg "):
            self.irc.send(bytes(f"PRIVMSG {message[5:]}\n", "UTF-8"))
        else:
            self.irc.send(bytes(f"PRIVMSG {self.channel} :{message}\n", "UTF-8"))

    def closeEvent(self, event):
        self.irc.close()
        self.thread_running.clear()
        event.accept()

def main():
    app = QApplication(sys.argv)

    server, channel, botnick = get_server_details()

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.settimeout(60.0)
    
    try:
        irc.connect((server, 6667))
        irc.send(bytes(f"NICK {botnick}\n", "UTF-8"))
        irc.send(bytes(f"USER {botnick} 0 * :{botnick}\n", "UTF-8"))
    except socket.error:
        sys.exit("Could not connect to the server. Please restart the client.")

    thread_running = threading.Event()
    thread_running.set()

    client = IRCClient(irc, thread_running, channel)

    threading.Thread(target=receive_messages, args=(irc, client.text_edit, thread_running.is_set, channel)).start()

    client.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
