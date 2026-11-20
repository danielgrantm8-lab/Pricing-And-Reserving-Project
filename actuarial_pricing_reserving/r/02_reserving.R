# Chain Ladder reserving using the published RAA paid-loss triangle.
# This is a separate portfolio from the French motor pricing dataset.
if (!requireNamespace('ChainLadder', quietly = TRUE)) {
  install.packages('ChainLadder', repos = 'https://cloud.r-project.org')
}
dir.create('outputs', showWarnings = FALSE)
data('RAA', package = 'ChainLadder')
triangle <- RAA
n <- nrow(triangle)
stopifnot(n == ncol(triangle))

# Age-to-age development factors, calculated manually from observed cells.
factors <- numeric(n - 1)
for (j in seq_len(n - 1)) {
  available <- which(!is.na(triangle[, j]) & !is.na(triangle[, j + 1]))
  factors[j] <- sum(triangle[available, j + 1]) / sum(triangle[available, j])
}
stopifnot(all(is.finite(factors)), all(factors > 0))

# Project each origin year's latest paid cumulative claim to ultimate.
latest <- numeric(n)
ultimate <- numeric(n)
for (i in seq_len(n)) {
  observed <- which(!is.na(triangle[i, ]))
  last_age <- max(observed)
  latest[i] <- triangle[i, last_age]
  remaining <- if (last_age < n) prod(factors[last_age:(n - 1)]) else 1
  ultimate[i] <- latest[i] * remaining
}
reserve <- ultimate - latest
results <- data.frame(origin_year = seq_len(n), latest_paid = latest,
                      ultimate = ultimate, outstanding_reserve = reserve)
stopifnot(all(abs(results$ultimate - results$latest_paid - results$outstanding_reserve) < 1e-7))
write.csv(results, 'outputs/reserve_estimates.csv', row.names = FALSE)
write.csv(data.frame(development_age = seq_len(n - 1), factor = factors),
          'outputs/development_factors.csv', row.names = FALSE)

# Independently compare with the ChainLadder package's deterministic result.
package_result <- ChainLadder::MackChainLadder(triangle, est.sigma = 'Mack')
package_ultimate <- as.numeric(package_result$FullTriangle[, n])
stopifnot(isTRUE(all.equal(ultimate, package_ultimate, tolerance = 1e-6)))
cat('Total outstanding reserve:', round(sum(reserve), 2), '\n')
cat('Manual Chain Ladder agrees with ChainLadder package.\n')
print(results)
