/**
 * Author: Matt Christie, 2015-2016
 *
 * A database used to hold the data generated in the experiment.
 */

-- Wipe database
DROP TABLE IF EXISTS Graph;
DROP TABLE IF EXISTS Permutation;
DROP TABLE IF EXISTS GroupClass;
DROP TABLE IF EXISTS PermGroup;
DROP TABLE IF EXISTS GroupElement;
DROP TABLE IF EXISTS Histogram;
DROP TABLE IF EXISTS Trial;

CREATE TABLE IF NOT EXISTS Graph (
	id INTEGER PRIMARY KEY, -- The graph encoded as an integer
	nodes INTEGER,
	edges INTEGER
	-- Other attributes? Max degree of a node?
);

CREATE TABLE IF NOT EXISTS Permutation (
	id INTEGER PRIMARY KEY, -- The permutation encoded as an integer
	cycle_decomp INTEGER -- The cycle decomposition count encoded as an integer
);

/* Cycle decomposition histograms for groups, representation 1 */
CREATE TABLE IF NOT EXISTS GroupClass (
	id INTEGER PRIMARY KEY, -- Possibly arbitrary identifier
	repr TEXT,              -- Unique JSON representation
	size INTEGER
);

CREATE UNIQUE INDEX IF NOT EXISTS GroupClassRepr ON GroupClass(repr);

/* Groups of permutations, representation 1 */
CREATE TABLE IF NOT EXISTS PermGroup (
	id INTEGER PRIMARY KEY, -- Possibly arbitrary identifier
	repr TEXT,              -- Unique JSON representation as a list of integers
	cls INTEGER REFERENCES GroupClass(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS GroupRepr ON PermGroup(repr);

/* Groups of permutations, representation 2 */
CREATE TABLE IF NOT EXISTS GroupElement (
	grp INTEGER REFERENCES PermGroup(id),
	elt INTEGER REFERENCES Permutation(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS UniqueGroupElement ON GroupElement(grp, elt);
CREATE INDEX IF NOT EXISTS ElementAccess ON GroupElement(elt);

/* Cycle decomposition histograms for groups, representation 2 */
CREATE TABLE IF NOT EXISTS Histogram (
	id INTEGER REFERENCES GroupClass(id),
	decomp INTEGER,         -- Sequence of integers encoded as an integer
	count INTEGER
);

CREATE UNIQUE INDEX IF NOT EXISTS UniqueHistogram ON Histogram(decomp, count, id);
CREATE INDEX IF NOT EXISTS Fingerprint ON Histogram(id);

/* Finally, the meat of the database: instances of the experiment */
CREATE TABLE IF NOT EXISTS Trial (
	id INTEGER PRIMARY KEY, -- Arbitrary identifier
	graph INTEGER REFERENCES Graph(id),
	nodes INTEGER,          -- A subset of the nodes of the graph encoded as an integer
	method CHAR(4),
	grp INTEGER REFERENCES PermGroup(id),
	datetime REAL
);

CREATE UNIQUE INDEX IF NOT EXISTS UniqueTrial ON Trial(graph, nodes, method, datetime);
CREATE INDEX IF NOT EXISTS TrialTime ON Trial(datetime);

