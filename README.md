# Hackathon Project by Skyline 2001


### Start the frontend
```sh
scripts/start_frontend.py
```

### Start the backend
```sh
scripts/start_backend.py
```
Keep both running simultaneously

    
### Refresh python packages
```sh
cd backend
pip install -r requirements.txt
```
### After adding a new python package, update the requirements.txt file
```sh
cd backend
pip freeze > requirements.txt
```

### Refresh node packages
```sh
cd frontend/HackathonProject
npm install
```

### Start MongoDB server
```sh
sudo systemctl start mongod
```
