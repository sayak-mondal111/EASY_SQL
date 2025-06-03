import pymysql
import json

class serverConnect():
    def __init__(self):
        database_credentials={}

        with open('database_credentials.json','r') as f:
            database_credentials=json.loads(f.read())

        if not database_credentials:
            print("database_credentials,json is missing or file is empty")
            return

        self.host=database_credentials['host']
        self.user=database_credentials['user']
        self.password=database_credentials['password']
        self.database=database_credentials['database']
        

    def connect_server(self):
        try:
            self.conn = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset="utf8mb4"
                )
        except pymysql.MySQLError as e:
            print(f"Error: {e}")

    def fetch_database_structure(self)->dict['table':{'field':[str]}]:
        try:
            self.connect_server()
            cursor = self.conn.cursor()
            # Fetch all tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            print("Successfully connected to MySQL!")
            #print("Tables in database SNU:")

            # Dictionary to store table structures
            database_structure = {}

            for table in tables:
                table_name = table[0]
                #print(f"\nTable: {table_name}")
                
                # Fetch table schema
                cursor.execute(f"DESC {table_name};")
                columns = cursor.fetchall()

                # Dictionary to store column details
                column_details = {}

                for col in columns:
                    field_name = col[0] if col[0] else ""
                    field_type = col[1] if col[1] else ""
                    is_nullable = col[2] if col[2] else ""
                    key_type = col[3] if col[3] else ""  # Handle None
                    extra = col[4] if col[4] else ""  # Handle None

                    # Store column details in dictionary
                    column_details[field_name] = [field_type, is_nullable, key_type, extra]

                    # Print column details
                    #print(f"| {field_name:<14} | {field_type:<15} | {is_nullable:<4} | {key_type:<3} | {extra:<6} |")

                #print("--------------------------------------------------------")

                # Store in main dictionary
                database_structure[table_name] = column_details

            # Print dictionary
            #print("\nDatabase Structure as Dictionary:")
            #for table,disc in database_structure.items():
            #    print(f"{table}: {disc}\n")

            # Close connection
            cursor.close()
            self.conn.close()
            return database_structure

        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            cursor.close()
            self.conn.close()
            return []


    #print(fetch_database_structure())



    # def runQuery(self,query):
    #     try:
    #         self.connect_server()
    #         print(f"Query is : {query}")
    #         cursor = self.conn.cursor()

    #         # Fetch all tables
    #         cursor.execute(query)
    #         column = cursor.fetchall()
    #         cursor.close()
    #         self.conn.close()
    #         return column
            
    #     except pymysql.MySQLError as e:
    #         print(f"Error: {e}")
    #         cursor.close()
    #         self.conn.close()
    #         return []

    def runQuery(self, query):
        try:
            self.connect_server()
            #print(f"Query is: {query}")
            cursor = self.conn.cursor()

            # Execute the query
            cursor.execute(query)

            # Fetch column names from the cursor description
            columns = [column[0] for column in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert rows to a list of lists (each row is a list of values)
            data = [list(row) for row in rows]

            cursor.close()
            self.conn.close()
            return [columns, data]  # Return [field_names, data_rows]

        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            if cursor:
                cursor.close()
            if self.conn:
                self.conn.close()
            return [[], []]  # Return empty lists in case of error

obj = serverConnect()
print(obj.fetch_database_structure(),"\n")
#query="select name from student;"
#print(obj.runQuery(query))
