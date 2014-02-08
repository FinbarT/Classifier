import urllib.request       # module for handling http: requests
import csv                  # module for handling .csv files


class classifier(object):
    """
    Classifier object, capable of handling .csv sourced from either
    http or a file. It makes predictions on peoples income from list of
    records based on weighted vaules given to each attribute in each
    record
    """
    def __init__(self, source, split):
        """
        Constructor/ initialiser method. It takes 2 arguments source
        and split. Source is a string and can either be a filename or
        a URL. This represents the location of the .csv data. Split
        represents the % split needed to to divide the data into
        training and test sets
        """
        self.data_set = self.get_data(source)
        self.weighted_data_set = self.weight_data(self.data_set)
        split = int((
            split / 100
            ) * len(self.weighted_data_set)
        )
        self.test_data = self.weighted_data_set[:split]
        self.training_data = self.weighted_data_set[split:]
        self.avg_record = self.get_avg_rec(self.training_data)

    def __str__(self):
        """
        Defines how the object should react when string
        is called on it. If this was not defined, python would
        default to the __repr__ method in it's place
        """
        return("Classifier object")

    def __repr__(self):
        """
        Defines a representation of this classifier object
        """
        return("Classifier object")

    def get_data(self, source):
        """
        This method retrieves the .csv data from the given source.
        Source is a string, either a filename or URL. It reurns a
        list of dict's containing all the comma serpared values
        """
        try:
            if source[:5] == "http:":   # if source is a URL
                source = self.source_from_url(source)
            else:
                pass
            data = csv.reader(open(source, 'r'))

            return [{
                    'age': row[0],                   # already numeric
                    'workclass': row[1][1:],         # needs converting
                    'education_num': row[4][1:],     # needs converting
                    'marital_status': row[5][1:],    # needs converting
                    'occupation': row[6][1:],        # needs converting
                    'relationship': row[7][1:],      # needs converting
                    'race': row[8][1:],              # needs converting
                    'sex': row[9][1:],               # needs converting
                    'capital_gain': row[10][1:],     # already numeric
                    'capital_loss': row[11][1:],     # already numeric
                    'hours_per_week': row[12][1:],   # already numeric
                    'outcome': row[14][1:]           # retained as is
                } for row in data if len(row) == 15  # if cators
            ]                                        # for empty or
                                                     # incomplete lines
        except (
            IOError,
            urllib.error.URLError,
            FileNotFoundError,
            UnicodeDecodeError
        ):
            print(
                """
                .CSV File Source error: {}
                This program will now exit gracefully
                """.format(source)
            )
            self.quit_prog()   # exit

    def source_from_url(self, url):
        """
        Method that takes a url string and returns a file object
        """
        f, h = urllib.request.urlretrieve(url)
        return f

    def quit_prog(self):
        """
        Method to exit the program gracefully, should any errors occour
        """
        import os
        os._exit(0)

    def weight_data(self, data):
        """
        Method to add numeric weighted to the string attributes. It
        takes a list of dict's that have non numeric attributes and
        returns a list of dict's with numeric values in place of the
        strings
        """
        # numeric id added to each dict in the list so
        # we can regain the same order again later
        for record in data:
            record['id_tag'] = str(data.index(record))

        positives, negatives = self.separate(data)
        positives = self.enumerate_values(positives)
        negatives = self.enumerate_values(negatives)
        # creats a list from positives + negatives and sorts it
        # by the numeric id we gave it earlier
        lst = sorted(
            positives + negatives,
            key=lambda x: int(x['id_tag'])
        )
        # strips the numeric id tags again
        for record in lst:
            del(record['id_tag'])

        return lst

    def separate(self, lst):
        """
        This method takes a list of dict's and separates them
        into two lists based on whether the dict's have an attribut
        of >50K of <=50k. It then returns the two lists coupled
        together as a single list
        """
        positives, negatives = [], []

        for record in lst:
            if record['outcome'] == '>50K':
                positives.append(record)
            else:
                negatives.append(record)

        return [positives, negatives]

    def enumerate_values(self, lst):
        """
        This method takes a list of dicts and enumerates all the non
        numeric values in it except for the outcome. It then returns
        the list of dict's with all numeric attributes.
        """
        rec_totals = {}
        # this suite counts how many times each attribute appears in
        # each colume and saves it in rec totals. Each key in the
        # rec_totals represents a colume in the csv data. Each paired
        # value contains another dict inturn it's keys make up all the
        # possible attributes in that colume and it's values contain a
        # count how how many times each attribute appears in each
        # colume
        for record in lst:
            for key in record.keys():
                if not key in rec_totals:
                    rec_totals[key] = {record[key]: 1}
                elif not record[key] in rec_totals[key]:
                    rec_totals[key][record[key]] = 1
                else:
                    rec_totals[key][record[key]] += 1
        # this suite replaces all non numeric attributes with
        # the total number of times that attribute appears in that
        # colume divided by how many records there is in the list
        for rec in lst:
            for key in rec.keys():
                if (   # education number isn't a weighted numeric value
                    (not rec[key].isdigit() and key != 'outcome') or
                    key == 'education_num'
                ):
                    rec[key] = rec_totals[key][rec[key]] / len(lst)
                else:
                    continue
        return lst

    def get_avg_rec(self, lst):
        """
        Takes a list of dicts, gets an average record for those who
        earn over 50k and an average recod for those who earn under
        50k then returns an average of the two, setting "the bar" for
        our classifier object for use to compare our test_data to
        """
        average = lambda x: {
            key: sum(
                float(rec[key])
                for rec in x
            ) / len(x)
            for key in x[0].keys() if key != 'outcome'
        }
        positives, negatives = self.separate(lst)

        return average([average(positives), average(negatives)])

    def classify(self):
        """
        Method compares all the records in our test data against the
        average record we got from our training data. It then guesses
        whether someone earns over 50k or under 50k based on the
        compasion. Returns a % value for the amount of times it guessed
        correctly
        """
        pos, neg = 0, 0
        for rec in self.test_data:
            higher, lower = 0, 0
            for key in rec.keys():
                if key in self.avg_record:
                    if float(rec[key]) <= self.avg_record[key]:
                        lower += 1
                    else:
                        higher += 1
                else:
                    continue
            if (
                (lower < higher and rec['outcome'] == ">50K") or
                (lower >= higher and rec['outcome'] == "<=50K")
            ):
                pos += 1
            else:
                neg += 1

        return pos/len(self.test_data) * 100


def main():
    """
    Main function to drive the classifier class. It just creates and
    instance of classifier called my_classifier. It calls the
    .classify() Method and prints the result
    """
    filename = "records.csv"
    url = "http://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
    percentage_split_for_test_data = 25
    # classifier can take either a filename or url and automatically
    # source the data.
    my_classifier = classifier(url, percentage_split_for_test_data)
    print(my_classifier.classify())

if __name__ == "__main__":
# This just makes sure if this module is being called directly from the
# command line that main gets run. If I imported this module into another
# module to use classifer with other code, then main would not get run.
    main()
