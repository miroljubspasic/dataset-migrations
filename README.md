# Docker Solution for dataset migration

**Docker solution** app will ensure and provide all requirements needed for dataset migration. It will generate required formats (xml/json) depending on type of data, and set required file size limit (each under 100 MB).  Installation is available through two different methods.

##
## 1. Method Installation - Docker desktop app (recommended)

- Download and install docker desktop app (available for all platforms) from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
- Start Docker app and let service run in background
- Clone git repo → `git clone https://github.com/miroljubspasic/dataset-migrations.git`
- Navigate to `dataset-migration/app` folder and duplicate **.env.example** file
- Rename one of these files to just “**.env**” (it will become hidden file by system defaults)
- **Important**, don't move/remove or edit the .env.example file
- If necessary, change your folder view options in order to see **.env** file again
- Overwrite new **.env** file with the received one --> edit/change:
	- API_URLs
	- .env params

### Initial setup

- Open terminal/command line and navigate to `dataset-migration/app` folder

Run the following commands for startup:
- `docker-compose build` (this command is only run the first time)
- `docker-compose up -d`
    
When docker initialisation is finished and container is set, you can proceed to extractions/exports

### API endpoints --> command list

Command list depending of an endpoint:
-   Customers: `docker exec -it app dataset start --type=customers`    
-   Orders: `docker exec -it app dataset start --type=orders`    
-   Giftcards: `docker exec -it app dataset start --type=giftcards`    
-   Subscriptions: `docker exec -it app dataset start --type=sor_subscriptions`    
-   Sub Orders: `docker exec -it app dataset start --type=sor_orders`

### User flow

When starting the command just follow the onscreen instructions. If process is interrupt in any way, you always can continue where you left off by entering the same command, app will ask you if you want to continue with the same job_ID (by clicking “y”) or to start all over again, with a new one (by clicking “n”). Possible errors during the process are with status “**500**” or “**502**” due to the network/connection timeout.

When an error is detected, it will ask you if you want to try again -> click “y”. It will just continue where it left off. If the same error occurs too many times in a row, please report it to us, so we can check the status of the server/website.

### Results

Each export will get its job ID (for easier overview)
Results will be placed in the `dataset-migration/app/results` folder, under each endpoint name subfolder. For example: `dataset-migration/app/results/customers`
Result layout contains a folder (job_ID) with original files and **.zip** file which contains compressed files, each under 100 MB.
##
## 2. Method - Installation - Python (optional)

### Tested with Python v3.8
- Clone git repo → `git clone https://github.com/miroljubspasic/dataset-migrations.git`
- Navigate to `dataset-migration/app` folder and duplicate **.env.example** file
- Rename one of these files to just “**.env**” (it will become hidden file by system defaults)
- **Important**, don't move/remove or edit the .env.example file
- Overwrite new **.env** file with the received one --> edit/change:
	- API_URLs
	- .env params
- Open terminal/command line and navigate to `dataset-migration/app` folder
- `pip install --editable .`
- `dataset start --type=customers`
- `dataset start --type=orders`
- `dataset start --type=giftcards`
- `dataset start --type=sor_subscriptions`
- `dataset start --type=sor_orders`
