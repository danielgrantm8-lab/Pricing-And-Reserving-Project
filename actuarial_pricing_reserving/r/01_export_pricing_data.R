# Run from project root. Downloads the published French motor pricing data
# using CASdatasets, then exports CSV files for the Python analysis.
if (!requireNamespace('CASdatasets', quietly = TRUE)) {
  install.packages('CASdatasets', repos = 'https://cas.uqam.ca/pub/R/')
}
dir.create('data', showWarnings = FALSE)
data('freMTPL2freq', package = 'CASdatasets')
data('freMTPL2sev', package = 'CASdatasets')
write.csv(freMTPL2freq, 'data/freMTPL2freq.csv', row.names = FALSE)
write.csv(freMTPL2sev, 'data/freMTPL2sev.csv', row.names = FALSE)
cat('Exported', nrow(freMTPL2freq), 'policies and', nrow(freMTPL2sev), 'claims\n')
