"""
Analyzes the search data provided by Google. Expects standard JSON format.
Outputs a breakdown by query type and year/month statistic.

TODO:
- analyze "event" structure for additional information -> Maps search?
- GUI displaying tree: year | month | day/query | details
- cluster search terms -> how?
- proper CLI with arguments
- split up modules for data processing, GUI and CLI
"""

from __future__ import print_function
import json
import glob
from collections import defaultdict
import time
from copy import copy
show_gui = True

decoder = json.JSONDecoder()
query_types = defaultdict(lambda: 0)
query_times = defaultdict(lambda: defaultdict(lambda: 0))
query_tree = defaultdict(lambda: defaultdict(lambda: []))
total_queries = 0
query_terms = defaultdict(lambda: 0)
ignore_terms = ["in", "to", "a", "the"]

for filename in glob.glob("./Searches/Searches/*.json"):
    #print("parsing {file}".format(file=filename))
    with open(filename, 'r') as jsonFile:
        data = decoder.decode(jsonFile.readline())
        total_queries += len(data["event"])
        for event in data["event"]:
            query = event["query"]
            ids = query["id"]
            timestamp = ids[-1]["timestamp_usec"][:10]
            query_time = time.localtime(float(timestamp))
            query_times[query_time.tm_year][query_time.tm_mon] += 1
            query_tree[query_time.tm_year][query_time.tm_mon].append(query["query_text"].lower())
            if len(ids) > 1 and "type" in ids[0]:
                query_types[ids[0]["type"]] += 1
            else:
                query_types["TEXT"] += 1
            if "->" not in query["query_text"]: #  filtering out direction search TODO: does this work? maybe add new search type?
                for term in query["query_text"].split():
                    if term not in ignore_terms:
                        query_terms[term] += 1

def filter(query):
    query =query.strip().lower()
    global working_tree
    # TODO: redraw tree
    if query is not None and len(query) > 0:
        print("filtering by " + query)
        working_tree = filter_nested_dict(query_tree, query)
        print(working_tree)
    else:
        print("resetting filter")
        working_tree = {}  # TODO: just seeing if that works reset to query_tree

def filter_nested_dict(node, search_term):
    if isinstance(node, list):
        return [item for item in node if search_term in item]
    else:
        dupe_node = {}
        for key, val in node.iteritems():
            cur_node = filter_nested_dict(val, search_term)
            if cur_node:
                dupe_node[key] = cur_node
        return dupe_node or None

working_tree = copy(query_tree)
# TODO: month names should be converted automatically
months = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
top_terms = sorted(query_terms.items(), key=lambda t: t[1], reverse=True)

if show_gui:
    from Tkinter import *
    import ttk
    root = Tk()
    root.title("Google Data Analysis")
    textfield = Entry(root)
    textfield.bind("<Return>", lambda event: filter(textfield.get()))
    textfield.grid(row=0, column=0)
    filter_button = Button(root, text='Filter', command=lambda: filter(textfield.get()))
    filter_button.grid(row=0, column=1)
    reset_button = Button(root, text='Reset', command=lambda: filter(None))  # TODO: reset textfield
    reset_button.grid(row=0, column=2)
    expand_button = Button(root, text='Expand All', command=lambda: tree.item("", open=True))
    expand_button.grid(row=0, column=3)
    collapse_button = Button(root, text='Collapse All', command=lambda: tree.item("", open=False))
    collapse_button.grid(row=0, column=4)

    top_terms_label = Label(root, text="Top Terms")
    top_terms_label.grid(row=0, column=5)
    top_terms_select = Text(root)
    top_terms_select.insert(INSERT, "\n".join(u"{term}: {count}".format(term=term[0], count=term[1]) for term in top_terms))
    # TODO: add double click handler on top terms to filter: top_terms_select.bind("<Double-Button-1>")
    top_terms_select.grid(row=1, column=5, sticky=N+S)
    # TODO: add scroll bar

    tree = ttk.Treeview(root)
    #tree.heading('0', text="date")  # TODO: how to set heading of tree?
    tree["columns"]=("col1")
    tree.column("col1", width=100)
    tree.heading("col1", text="query count")
    tree.grid(row=1, column=0, columnspan=5, sticky=N+S+E+W)

    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)
    root.columnconfigure(3, weight=1)
    root.columnconfigure(4, weight=1)

    for year, year_data in query_times.items():
        year_item = tree.insert("", 0, text=year, values=(sum(year_data.values())))
        for month, count in sorted(year_data.items()):
            month_item = tree.insert(year_item, "end", "{y}_{m}".format(y=year, m=month), text=months[month], values=(count))
            for query in working_tree[year][month]:
                tree.insert(month_item, "end", text=query)
    root.mainloop()
else:
    print(u"total queries = {qcount}, {tcount} distinct terms".format(qcount=total_queries, tcount=len(query_terms)))
    print(u"top 10 terms: {top_terms}".format(top_terms=", ".join("{term} ({count})".format(term=k, count=v) for (k, v) in top_terms[:10])))
    print("\n".join("{type}: {count}".format(type=k, count=v) for (k, v) in query_types.items()))
    for year, year_data in query_times.items():
        print("{year} (total: {year_total})".format(year=year, year_total=sum(year_data.values())))
        print("\n".join("\t{month}: {count}".format(month=months[k], count=v) for (k, v) in sorted(year_data.items())))
