import shutil
import subprocess

shutil.make_archive("simulations", "zip", "../simulations")
subprocess.call(
    "ascp dev simulations.zip trans4num:/trans4num/src/data/simulations.zip",
    shell=True,
)

print(
    "Now ssh into the instance and run, and run: \n unzip /trans4num/src/data/simulations.zip -d /trans4num/src/data/simulations/"
)
