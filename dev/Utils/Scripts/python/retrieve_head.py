import sys
import argparse

parser = argparse.ArgumentParser(description="Clean data of WMT23",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-a", "--archive", action="store_true",
                    help="archive mode")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase verbosity")
parser.add_argument(
    "-c", "--corpus", help="Name of the corpus for special process")
parser.add_argument("-i", "--input-path", help="Input PATH")
parser.add_argument("-o", "--output-path", help="Output PATH")
parser.add_argument("-r", "--result-head", help="Output PATH for head")
parser.add_argument("-f", "--fill-size", type=int, default=None,
                    help="fill output with artificial heads every fill-size lines")
args = parser.parse_args()
config = vars(args)

with open(config["input_path"], "r") as f:
    data = f.read().split("\n")

if len(data) < 1 or data[0] != "":
    assert "bad data format (empty or begin with empty line)"

liste_head = []
nb_line = 0
nb_artificial_head = 0
# print(len(data))
# index_line = len(data) - 1


# # Process for WMT23
# if config['corpus'] == "WMT23":
#     while index_line >= 0:
#         # print(index_line)
#         # Si on est sur un début de chapitre/livre, on supprime la phrase
#         if data[index_line].startswith("<CHAPTER") or data[index_line] == "":
#             del data[index_line]
#             liste_head.append(str(index_line + 1))

#         # Si on est sur une fin de chapitre suivi du début d'un autre, on ajoute une ligne vide
#         elif data[index_line].startswith("</CHAPTER") \
#                 or data[index_line].startswith('</BOOK') \
#                 or data[index_line].startswith('<BOOK'):
#             del data[index_line]
#         index_line -= 1
# liste_head=reversed(liste_head)

index_line = 0
if config['corpus'] == "WMT23":
    while index_line < len(data) - 1:
        if data[index_line].startswith("<CHAPTER") \
                or data[index_line] == "" \
                or data[index_line] == " ":
            del data[index_line]
            liste_head.append(str(index_line + 1))
            index_line -= 1
        elif data[index_line].startswith("</CHAPTER") \
                or data[index_line].startswith('</BOOK') \
                or data[index_line].startswith('<BOOK'):
            del data[index_line]
            index_line -= 1
        index_line += 1


print("document : {}".format(config["input_path"]))
print("After adding artificial heads: ", len(liste_head))


# print(liste_head)
with open(config["output_path"], "w") as f:
    f.write("\n".join(data))
with open(config["result_head"], "w") as f:
    f.write("\n".join(liste_head))
