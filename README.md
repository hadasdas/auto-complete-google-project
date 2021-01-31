# auto-complete-google-project
This Auto-complete algorithm scans a directory called Archive, and from all 1504 files in it offers a completion of
the user's typing, taking into account typos (one typo per sentence), and returning the best matches first.
The big challenge was storage and retrieval in reasonable time while the user types.
We used pytrie's SortedStringTrie to store our data, which was so useful we didn't have to deal with page faults and such.
