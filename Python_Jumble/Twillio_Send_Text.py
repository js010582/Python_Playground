{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [
    {
     "ename": "KeyError",
     "evalue": "'AC8e2d55b60a3d29a6e200698d15cefd8f'",
     "output_type": "error",
     "traceback": [
      "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[0;31mKeyError\u001b[0m                                  Traceback (most recent call last)",
      "\u001b[1;32m/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb Cell 1'\u001b[0m in \u001b[0;36m<cell line: 8>\u001b[0;34m()\u001b[0m\n\u001b[1;32m      <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=2'>3</a>\u001b[0m \u001b[39mfrom\u001b[39;00m \u001b[39mtwilio\u001b[39;00m\u001b[39m.\u001b[39;00m\u001b[39mrest\u001b[39;00m \u001b[39mimport\u001b[39;00m Client\n\u001b[1;32m      <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=5'>6</a>\u001b[0m \u001b[39m# Find your Account SID and Auth Token at twilio.com/console\u001b[39;00m\n\u001b[1;32m      <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=6'>7</a>\u001b[0m \u001b[39m# and set the environment variables. See http://twil.io/secure\u001b[39;00m\n\u001b[0;32m----> <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=7'>8</a>\u001b[0m account_sid \u001b[39m=\u001b[39m os\u001b[39m.\u001b[39;49menviron[\u001b[39m'\u001b[39;49m\u001b[39mAC8e2d55b60a3d29a6e200698d15cefd8f\u001b[39;49m\u001b[39m'\u001b[39;49m]\n\u001b[1;32m      <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=8'>9</a>\u001b[0m auth_token \u001b[39m=\u001b[39m os\u001b[39m.\u001b[39menviron[\u001b[39m'\u001b[39m\u001b[39m57798e9baaae06e4779be6fca93bcdc6\u001b[39m\u001b[39m'\u001b[39m]\n\u001b[1;32m     <a href='vscode-notebook-cell:/home/js010582/git_work_workspace/Python_Playground/Python_Jumble/Twillio_Send_Text.ipynb#ch0000000?line=9'>10</a>\u001b[0m client \u001b[39m=\u001b[39m Client(account_sid, auth_token)\n",
      "File \u001b[0;32m/usr/lib64/python3.10/os.py:679\u001b[0m, in \u001b[0;36m_Environ.__getitem__\u001b[0;34m(self, key)\u001b[0m\n\u001b[1;32m    <a href='file:///usr/lib64/python3.10/os.py?line=675'>676</a>\u001b[0m     value \u001b[39m=\u001b[39m \u001b[39mself\u001b[39m\u001b[39m.\u001b[39m_data[\u001b[39mself\u001b[39m\u001b[39m.\u001b[39mencodekey(key)]\n\u001b[1;32m    <a href='file:///usr/lib64/python3.10/os.py?line=676'>677</a>\u001b[0m \u001b[39mexcept\u001b[39;00m \u001b[39mKeyError\u001b[39;00m:\n\u001b[1;32m    <a href='file:///usr/lib64/python3.10/os.py?line=677'>678</a>\u001b[0m     \u001b[39m# raise KeyError with the original key value\u001b[39;00m\n\u001b[0;32m--> <a href='file:///usr/lib64/python3.10/os.py?line=678'>679</a>\u001b[0m     \u001b[39mraise\u001b[39;00m \u001b[39mKeyError\u001b[39;00m(key) \u001b[39mfrom\u001b[39;00m \u001b[39mNone\u001b[39m\n\u001b[1;32m    <a href='file:///usr/lib64/python3.10/os.py?line=679'>680</a>\u001b[0m \u001b[39mreturn\u001b[39;00m \u001b[39mself\u001b[39m\u001b[39m.\u001b[39mdecodevalue(value)\n",
      "\u001b[0;31mKeyError\u001b[0m: 'AC8e2d55b60a3d29a6e200698d15cefd8f'"
     ]
    }
   ],
   "source": []
  }
 ],
 "metadata": {
  "interpreter": {
   "hash": "18a88444c60b15ade15f3b7412e27f94167feb3c1614f51d86ea18cdd9c556c6"
  },
  "kernelspec": {
   "display_name": "Python 3.10.4 ('ML')",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.4"
  },
  "orig_nbformat": 4
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
