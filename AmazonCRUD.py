# Lucas Justiniano
# Assignment 3.5 - Python Application Accessing a Column Family Database
#
#= Date: September 16, 2026
# Purpose: Use Python and the Cassandra driver to perform CRUD operations
# on an Amazon review column family database.
from cassandra.cluster import Cluster
import json
import os
# ---------------------------------------------------------
# Connect to Cassandra
# ---------------------------------------------------------
cluster = Cluster(["127.0.0.1"])
session = cluster.connect()
# ---------------------------------------------------------
# Create the Amazon keyspace and required tables
# ---------------------------------------------------------
def setup_database():
    print("\nCreating Amazon keyspace and tables...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS Amazon
        WITH replication = {
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }
    """)
    session.set_keyspace("amazon")
    session.execute("""
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id text PRIMARY KEY,
            product_id text,
            reviewer_id text,
            stars int,
            review_body text,
            review_title text,
            product_category text
        )
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS ProductCategories (
            product_id text PRIMARY KEY,
            stars int,
            language text,
            product_category text
        )
    """)
    print("Amazon keyspace created.")
    print("Reviews table created.")
    print("ProductCategories table created.")
# ---------------------------------------------------------
# Insert the JSON dataset into both Cassandra tables
# ---------------------------------------------------------
def import_data():
    session.set_keyspace("amazon")
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "dataset_en_dev.json"
    )
    print("\nImporting JSON dataset...")
    count = 0
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                review_id = str(record.get("review_id", ""))
                product_id = str(record.get("product_id", ""))
                reviewer_id = str(record.get("reviewer_id", ""))
                try:
                    stars = int(record.get("stars", 0))
                except (ValueError, TypeError):
                    stars = 0
                review_body = str(record.get("review_body", ""))
                review_title = str(record.get("review_title", ""))
                language = str(record.get("language", ""))
                product_category = str(record.get("product_category", ""))
                session.execute("""
                    INSERT INTO Reviews
                    (review_id, product_id, reviewer_id, stars,
                     review_body, review_title, product_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    review_id,
                    product_id,
                    reviewer_id,
                    stars,
                    review_body,
                    review_title,
                    product_category
                ))
                session.execute("""
                    INSERT INTO ProductCategories
                    (product_id, stars, language, product_category)
                    VALUES (%s, %s, %s, %s)
                """, (
                    product_id,
                    stars,
                    language,
                    product_category
                ))
                count += 1
            except Exception as error:
                print("Skipped a record:", error)
    print("Dataset import complete.")
    print("Records processed:", count)
# ---------------------------------------------------------
# Display all distinct product categories
# ---------------------------------------------------------
def display_categories():
    session.set_keyspace("amazon")
    rows = session.execute(
        "SELECT product_category FROM ProductCategories;"
    )
    categories = sorted({
        row.product_category
        for row in rows
        if row.product_category
    })
    print("\nProduct Category List:")
    for category in categories:
        print(category)
    print("\nTotal distinct categories:", len(categories))
# ---------------------------------------------------------
# Display count of reviews with 4 stars or higher
# for a user-entered product category
# ---------------------------------------------------------
def high_review_count():
    session.set_keyspace("amazon")
    category = input(
        "\nEnter a product category for 4+ star review count: "
    ).strip()
    rows = session.execute(
        "SELECT product_category, stars FROM ProductCategories;"
    )
    count = 0
    for row in rows:
        if (
            row.product_category == category
            and row.stars is not None
            and row.stars >= 4
        ):
            count += 1
    print(
        "\n4-star and higher reviews for",
        category + ":",
        count
    )
# ---------------------------------------------------------
# Display count of 1-star reviews for a user-entered
# product category
# ---------------------------------------------------------
def low_review_count():
    session.set_keyspace("amazon")
    category = input(
        "\nEnter a product category for 1-star review count: "
    ).strip()
    rows = session.execute(
        "SELECT product_category, stars FROM ProductCategories;"
    )
    count = 0
    for row in rows:
        if (
            row.product_category == category
            and row.stars == 1
        ):
            count += 1
    print(
        "\n1-star reviews for",
        category + ":",
        count
    )
# ---------------------------------------------------------
# Allow the user to enter and execute CQL SELECT statements
# ---------------------------------------------------------
def execute_select():
    session.set_keyspace("amazon")
    print("\nEnter a CQL SELECT statement.")
    print("Example: SELECT * FROM Reviews LIMIT 5;")
    query = input("CQL> ").strip()
    if not query.lower().startswith("select"):
        print("Only SELECT statements are allowed.")
        return
    try:
        rows = session.execute(query)
        print("\nQuery Results:")
        row_count = 0
        for row in rows:
            print(row)
            row_count += 1
        print("\nRows returned:", row_count)
    except Exception as error:
        print("CQL error:", error)
# ---------------------------------------------------------
# Add or remove table columns
# ---------------------------------------------------------
def alter_columns():
    session.set_keyspace("amazon")
    print("\n1. Add a column")
    print("2. Remove a column")
    choice = input("Choose an option: ").strip()
    table = input(
        "Enter table name (Reviews or ProductCategories): "
    ).strip()
    if table.lower() not in ["reviews", "productcategories"]:
        print("Invalid table name.")
        return
    if choice == "1":
        column = input("Enter new column name: ").strip()
        datatype = input(
            "Enter Cassandra data type (example: text or int): "
        ).strip()
        try:
            session.execute(
                f"ALTER TABLE {table} ADD {column} {datatype};"
            )
            print("Column added successfully.")
        except Exception as error:
            print("Unable to add column:", error)
    elif choice == "2":
        column = input("Enter column name to remove: ").strip()
        try:
            session.execute(
                f"ALTER TABLE {table} DROP {column};"
            )
            print("Column removed successfully.")
        except Exception as error:
            print("Unable to remove column:", error)
    else:
        print("Invalid option.")
# ---------------------------------------------------------
# Delete Reviews and ProductCategories tables
# ---------------------------------------------------------
def delete_tables():
    session.set_keyspace("amazon")
    confirm = input(
        "\nDelete Reviews and ProductCategories tables? (yes/no): "
    ).strip().lower()
    if confirm == "yes":
        session.execute(
            "DROP TABLE IF EXISTS Reviews;"
        )
        session.execute(
            "DROP TABLE IF EXISTS ProductCategories;"
        )
        print("Reviews table deleted.")
        print("ProductCategories table deleted.")
    else:
        print("Table deletion canceled.")
# ---------------------------------------------------------
# Delete the Amazon keyspace
# ---------------------------------------------------------
def delete_keyspace():
    confirm = input(
        "\nDelete the Amazon keyspace? (yes/no): "
    ).strip().lower()
    if confirm == "yes":
        session.execute(
            "DROP KEYSPACE IF EXISTS Amazon;"
        )
        print("Amazon keyspace deleted.")
    else:
        print("Keyspace deletion canceled.")
# ---------------------------------------------------------
# Display the user-driven application menu
# ---------------------------------------------------------
def display_menu():
    print("\n" + "=" * 60)
    print("Amazon Cassandra CRUD Application")
    print("=" * 60)
    print("Type in a number and press Enter to execute the menu option.")
    print("1. Display product category list")
    print("2. Display high (4+) star review count")
    print("3. Display low (1) star review count")
    print("4. Enter a query")
    print("5. Add/Remove table columns")
    print("6. Delete tables")
    print("7. Delete keyspace")
    print("8. Exit the program")
    print("=" * 60)
# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------
def main():
    try:
        setup_database()
        import_data()
        while True:
            display_menu()
            choice = input("Enter your choice: ").strip()
            if choice == "1":
                display_categories()
            elif choice == "2":
                high_review_count()
            elif choice == "3":
                low_review_count()
            elif choice == "4":
                execute_select()
            elif choice == "5":
                alter_columns()
            elif choice == "6":
                delete_tables()
            elif choice == "7":
                delete_keyspace()
            elif choice == "8":
                print("\nExiting program.")
                break
            else:
                print(
                    "\nInvalid selection. "
                    "Please enter a number from 1 through 8."
                )
    except Exception as error:
        print("\nProgram error:", error)
    finally:
        cluster.shutdown()
if __name__ == "__main__":
    main()
