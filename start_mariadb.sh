DATABASE_URI="mariadb+pymysql://root:]9sT3vn+&R(a$]bxD\"hWP^eHb@nas.prome.sg/synomail?charset=utf8mb4" poetry run flask db init
DATABASE_URI="mariadb+pymysql://root:]9sT3vn+&R(a$]bxD\"hWP^eHb@nas.prome.sg/synomail?charset=utf8mb4" poetry run flask db migrate -m "Init"
DATABASE_URI="mariadb+pymysql://root:]9sT3vn+&R(a$]bxD\"hWP^eHb@nas.prome.sg/synomail?charset=utf8mb4" poetry run flask db upgrade

