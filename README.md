# B-20

## Environment Setup

### Step 1: Verify Python version
Ensure that you have Python **3.11.5** installed. 

Your virtual environment will use whatever version of Python you create it with.
We will standardize on the latest stable release of Python, 3.11.5, as recommended by Django.

You can easily check your Python version using `python --version`. 
Ensure your output matches this:
```shell
$ python --version
Python 3.11.5
```

If you have multiple versions of `python` installed and don't want to default to 3.11 for whatever reason,
ensure you can replicate the above output with `python3.11` instead of `python` or something similar. 

### Step 2: Create your virtual environment
```shell
$ python -m venv venv
```

If you want to name it something else, just ensure that your virtual environment directory will be gitignored.
The documentation suggests `.venv`, Pycharm defaults to `venv`.

### Step 3: Install required packages
```shell
$ python -m pip install -r requirements.txt
```

### Step 4: Test basic functionality
I suggest starting the application and navigating to [localhost:8000/deploytest](http://localhost:8000/deploytest/)
and entering some signatures to ensure things run smoothly and local database writes work.

You could also run the available tests as a sanity check.