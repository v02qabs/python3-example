import ftplib

ftp = ftplib.FTP("ftp.chobi.net")
ftp.set_pasv('true')
ftp.login("hirofumi090","hirofumi090Abc")

