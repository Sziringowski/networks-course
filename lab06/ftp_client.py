from ftplib import FTP
import os

def connect_ftp(server, username, password):
    ftp = FTP()
    ftp.connect(server)
    ftp.login(username, password)
    return ftp

def list_files(ftp):
    try:
        print("\ndirectory listing:")
        ftp.dir()
    except Exception as e:
        print(f"error: {str(e)}")

def upload_file(ftp):
    local_path = input("enter local file path: ")
    if not os.path.exists(local_path):
        print("error: file not found")
        return

    remote_name = os.path.basename(local_path)
    try:
        with open(local_path, 'rb') as file:
            ftp.storbinary(f'STOR {remote_name}', file)
        print("file uploaded successfully!")
    except Exception as e:
        print(f"error: {str(e)}")

def download_file(ftp):
    remote_name = input("enter remote file name: ")
    local_path = input("enter local save path: ")
    
    try:
        with open(local_path, 'wb') as file:
            ftp.retrbinary(f'RETR {remote_name}', file.write)
        print("file downloaded successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    server = "127.0.0.1"
    username = "TestUser"
    password = ""

    ftp = connect_ftp(server, username, password)
    
    while True:
        print("\nFTP client menu:")
        print("1. list files/directories")
        print("2. upload file")
        print("3. download file")
        print("4. exit")
        
        choice = input("select option: ")
        
        if choice == '1':
            list_files(ftp)
        elif choice == '2':
            upload_file(ftp)
        elif choice == '3':
            download_file(ftp)
        elif choice == '4':
            ftp.quit()
            break
        else:
            print("invalid option")

if __name__ == "__main__":
    main()