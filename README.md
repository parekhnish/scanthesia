# Scanthesia
Converting your favourite Synthesia (or Synthesia-like) piano videos into MIDI files



## Development
_This project uses [`pipenv`](https://pipenv.kennethreitz.org/) for managing dependencies and development environments._

You will need the `dev` packages to test the code. Navigate to the Scanthesia root directory and use `pipenv install --dev`.

### Testing

- Download the test data from [here](https://www.dropbox.com/s/41tkjzl2j4txopr/scanthesia_test_data.zip?dl=0). Extract the `.zip` file to a location of your choice.
- Navigate to the Scanthesia root directory, enter the `pipenv` environment and run the tests
  ```
  cd /path/to/scanthesia
  pipenv shell
  pytest --datadir=/path/to/test/data/scanthesia_test_data
  ```