function readEntryContentAsync(entry) {
    return new Promise((resolve, reject) => {
        let reading = 0;
        const contents = [];

        readEntry(entry);

        function readEntry(entry) {
            if (entry.isFile) {
                reading++;
                entry.file(file => {
                    reading--;
                    contents.push(file);

                    if (reading === 0) {
                        resolve(contents);
                    }
                });
            } else if (entry.isDirectory) {
                readReaderContent(entry.createReader());
            }
        }

        function readReaderContent(reader) {
            reading++;

            reader.readEntries(function (entries) {
                reading--;
                for (const entry of entries) {
                    readEntry(entry);
                }

                if (reading === 0) {
                    resolve(contents);
                }
            });
        }
    });
}