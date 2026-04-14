import pandas as pd

dataset_A = pd.read_csv('2_1/train.csv')
dataset_B = pd.read_csv('2_2/cyberbullying_tweets.csv')

print(dataset_A.info())
print(dataset_A.head(10))
print("-------------------------------------------\n")
print(dataset_A.columns)
print(dataset_A["toxic"].unique())
print(dataset_A["severe_toxic"].unique())
print(dataset_A["obscene"].unique())
print(dataset_A["obscene"].unique())
print(dataset_A["insult"].unique())
print(dataset_A["identity_hate"].unique())

print("===========================================\n")

print(dataset_B.info())
print(dataset_B.head(10))
print("-------------------------------------------\n")
print(dataset_B.columns)
print(dataset_B["cyberbullying_type"].unique())

dataset_A = dataset_A.dropna().drop_duplicates()
dataset_B = dataset_B.dropna().drop_duplicates()

dataset_A.to_csv("dataset_A.csv", index=False)

dataset_B.loc[(dataset_B.cyberbullying_type == "religion"), "cyberbullying_type"] = int(0)
dataset_B.loc[(dataset_B.cyberbullying_type == "age"), "cyberbullying_type"] = int(1)
dataset_B.loc[(dataset_B.cyberbullying_type == "gender"), "cyberbullying_type"] = int(2)
dataset_B.loc[(dataset_B.cyberbullying_type == "ethnicity"), "cyberbullying_type"] = int(3)
dataset_B.loc[(dataset_B.cyberbullying_type == "not_cyberbullying"), "cyberbullying_type"] = int(4)
dataset_B.loc[(dataset_B.cyberbullying_type == "other_cyberbullying"), "cyberbullying_type"] = int(5)

dataset_B.to_csv("dataset_B.csv", index=False)