import csv

from flask import Blueprint, jsonify

from sqlalchemy.exc import SQLAlchemyError

from app.models.memory import Memory

memory_db_csv_bp = Blueprint('memory_csv', __name__)

CSV_FILE_PATH = 'memory_conversations.csv'
LAST_MEMORY_CSV_FILE_PATH = 'last_memory_conversations.csv'


# Function to save the whole database data to CSV file
def save_database_to_csv():
    try:
        # Retrieve all memories from the database
        all_memories = Memory.query.all()

        # Open the CSV file in written mode
        with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
            fieldnames = ['owner_id', 'user_name', 'user_message', 'llm_response', 'conversations_summary',
                          'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write each memory to the CSV file
            for memory in all_memories:
                writer.writerow({
                    'owner_id': memory.owner_id,
                    'user_name': memory.user_name,
                    'user_message': memory.user_message,
                    'llm_response': memory.llm_response,
                    'conversations_summary': memory.conversations_summary,
                    'created_at': memory.created_at,
                })

    except SQLAlchemyError as err:
        # Log the exception or handle it as needed
        print(f"Error saving to CSV file: {str(err)}")


def save_last_memory_to_csv():
    try:
        # Retrieve the last memory from the database based on id
        last_memory = Memory.query.order_by(Memory.id.desc()).first()

        # Open the CSV file in written mode
        with open(LAST_MEMORY_CSV_FILE_PATH, 'a', newline='') as csvfile:
            fieldnames = ['owner_id', 'user_name', 'user_message', 'llm_response', 'conversations_summary',
                          'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the last memory to the CSV file
            writer.writerow({
                'owner_id': last_memory.owner_id,
                'user_name': last_memory.user_name,
                'user_message': last_memory.user_message,
                'llm_response': last_memory.llm_response,
                'conversations_summary': last_memory.conversations_summary,
                'created_at': last_memory.created_at,
            })

    except SQLAlchemyError as err:
        # Log the exception or handle it as needed
        print(f"Error saving to CSV file: {str(err)}")


@memory_db_csv_bp.route('/save-database-to-csv', methods=['GET'])
def save_database_to_csv_route():
    # Call the function to save the last memory to CSV
    save_database_to_csv()
    return jsonify({"message": "Data saved to CSV file."})
