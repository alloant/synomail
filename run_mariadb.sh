#DATABASE_URI="mariadb+pymysql://Aes:sG1zDL%=W]W(l-d\$|-yxzVEJ@nas.prome.sg/synomail?charset=utf8mb4" poetry run waitress-serve --threads=6 --host=100.97.32.113 --port=8041 --call 'app:create_app'
DATABASE_URI="mariadb+pymysql://root:]9sT3vn+&R(a$]bxD\"hWP^eHb@nas.prome.sg/synomail?charset=utf8mb4" poetry run waitress-serve --threads=6 --host=100.97.32.113 --port=8041 --call 'app:create_app'

