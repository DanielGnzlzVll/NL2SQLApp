# NL2SQLApp

This is a simple application which attempts to test natural language to SQL technique.

## Setup

Follow these steps to set up and run the application:

1. **Requirements**:
    Ensure you have the following dependencies installed:
   - docker
   - make

2. **Start the project**:
   - Open a terminal in the root directory of your project.
   - Execute the following command to initiate the project setup:
        ```bash
        make start
        ```

3. **Populate the Database**:

    After the database is created and necessary models are downloaded, proceed with the following steps:

    - Start a bash session in the main container using:
        ```bash
        make up
        ```

    - Once inside the container, populate the database by running:
        ```bash
        python manage.py load_data tsla_2014_2023.csv
        ```

    You can load any files available in the root repository.

3. **Start the web server**:
    After ensuring everything is properly set up, initiate the web server by running:
        ```bash
        make runserver
        ```


## Testing

To test the application, follow these steps:

1. **Access the application**:
   - Open a web browser and navigate to http://localhost:8000/api/v1/resolve_query/?q=XXX, replacing XXX with your actual question.


