!! BEFORE RUNNING CHANGE MYSQL LOGIN !!


installs required for running:
    
    install pip on mac:
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python get-pip.py
    
    install pip on windows:
        follow these instructions: https://www.geeksforgeeks.org/how-to-install-pip-on-windows/
        
    pip install spotipy
    pip install pandas
    pip install pandastable
    pip install flask



** Created Spotify API pull for user information **

** Created Spotify API pull for users Top 50 songs **


main.py
    - runs the flask app
    - pulls user information and top 50 songs
    - displays user information and top 50 songs in a table

app.py
    - contains the flask app
    - contains the routes for the app
    - contains the functions for the routes

database_manager.py
    - contains the functions for connecting to the database
    - contains the functions for creating the database
    - contains the functions for inserting data into the database
    - contains the functions for selecting data from the database

templates/index.html
    - contains the html for the app (web popup)
    - contains the css for the app (web popup)
    - contains the javascript for the app (web popup)

- ang

