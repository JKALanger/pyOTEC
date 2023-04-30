# pyOTEC

pyOTEC designs ocean thermal energy conversion (OTEC) plants for best economic performance under off-design conditions, meaning seasonal fluctuation of ocean thermal energy resources.

## Step-by-step guide to set up and use pyOTEC

1. If you don't have it yet, download the latest version of Anaconda
2. Install the netCDF4 library by first opening Anaconda prompt and then executing the following command
         
            conda install netCDF4
         
         3. Go to https://github.com/JKALanger/pyOTEC and download the repository to your computer
         4. Go to https://marine.copernicus.eu/ and create an account for free (you need the account to download the seawater temperature data)
         5. One of the files in pyOTEC is called credentials.txt. Go to that file and enter your username and password from the Copernicus account
         6. In Anaconda prompt, run the following command:

            python -m pip install motuclient==1.8.4 --no-cache-dir
 
            This installs the so called MOTU client which is used to connect to Copernicus’ server and download the data.
         
         7. Open the pyOTEC.py file in your preferred Python IDE (e.g. Spyder)
         8. Run the script and follow the instructions given by pyOTEC (i.e. provide the country and plant size)
         9. If you want to check or change the parameters used by the model, go to file parameters_and_constants.py


## Citation

When using pyOTEC, e.g. in a scientific publication, please refer to this GitHub repository and the following paper (April 2023: still under review, will be added soon)

Langer J, Blok K. The global techno-economic potential of floating, closed-cycle ocean thermal energy conversion. Under review.
