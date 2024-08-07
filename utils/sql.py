import sqlite3
import time


class Database:
    def __init__(self, database_name) -> None:
        self.database_name = database_name

    def init(self):
        self.conn = sqlite3.connect(self.database_name)
        self.c = self.conn.cursor()
        self.c.execute(
            '''CREATE TABLE RECORD
                (TIME INT PRIMARY KEY NOT NULL,
                TEMPERATURE FLOAT,
                HUMIDITY FLOAT,
                PRESSURE FLOAT,
                LUX FLOAT,
                UV FLOAT,
                GAS FLOAT,
                ROLL FLOAT,
                PITCH FLOAT,
                YAW FLOAT,
                ACCELERATION_X FLOAT,
                ACCELERATION_Y FLOAT,
                ACCELERATION_Z FLOAT,
                GYROSCOPE_X FLOAT,
                GYROSCOPE_Y FLOAT,
                GYROSCOPE_Z FLOAT,
                MAGNETIC_X FLOAT,
                MAGNETIC_Y FLOAT,
                MAGNETIC_Z FLOAT
                );'''
        )
        self.conn.commit()
        self.conn.close()

    def insert(self, data):
        self.conn = sqlite3.connect(self.database_name)
        self.c = self.conn.cursor()
        values = ','.join([str(d) for d in data])
        command = f'''INSERT INTO RECORD (TIME,TEMPERATURE,HUMIDITY,PRESSURE,LUX,UV,GAS,ROLL,PITCH,YAW, \
            ACCELERATION_X,ACCELERATION_Y,ACCELERATION_Z,GYROSCOPE_X,GYROSCOPE_Y,GYROSCOPE_Z,MAGNETIC_X,MAGNETIC_Y,MAGNETIC_Z) \
        VALUES ({int(time.time())},{values})'''
        self.c.execute(command)
        self.conn.commit()
        self.conn.close()

    def exec(self, cmd):
        self.conn = sqlite3.connect(self.database_name)
        self.c = self.conn.cursor()
        self.c.execute(cmd)
        self.conn.commit()
        self.conn.close()
