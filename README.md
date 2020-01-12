# Scanthesia
Converting your favourite Synthesia (or Synthesia-like) piano videos into MIDI files



## Development
This project uses [`pipenv`](https://pipenv.kennethreitz.org/) for managing dependencies and development environments.
<br>
You will need the `dev` packages to test the code. Navigate to the Scanthesia root directory and use `pipenv install --dev`.

### The `scripts` directory
Use this directory to store code that you write and use for purposes that you do not intend to commit to the repository.
Usually, these include scripts for experimentation, trying out new things, etc. A `.gitignore` file in the `scripts` directory will ensure that no files in it will get committed.

### Testing

- Download the test data from [here](https://www.dropbox.com/s/41tkjzl2j4txopr/scanthesia_test_data.zip?dl=0). Extract the `.zip` file to a location of your choice.
- Navigate to the Scanthesia root directory, enter the `pipenv` environment and run the tests
  ```bash
  cd /path/to/scanthesia
  pipenv shell
  pytest --datadir=/path/to/test/data/scanthesia_test_data
  ```