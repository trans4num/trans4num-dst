#set heading(numbering: "1.a")

#align(center, text(17pt)[ *Notes on crop rotation optimization problem* ])

= Initial problem description and formulation <initial>

We consider the problem of finding an optimal allocation of crops to different
fields for a single year in respect to maximizing the combined #emph[profit].
Later on we will introduce additional constraints, that for example restricts
the combined emission. The problem can without loss of generalization be swapped
to minimizing emission with an constraint on economy, so one can think of profit
as not necessarily in monetary terms, but some utility function we are
interested in maximizing.

We denote the amount of fields by $F$ and set of all fields $FF = {1, 2,..., F}$
and similarly the amount of different crops by $C$ and set $CC$. The expected
profit of planting a crop $c$ on a field $f$ is denoted $p_(c, f)$.

This can be formulated as the following #emph[Integer Linear Program] (ILP):

$
max_x &sum_(f=1)^F sum_(c=1)^C p_(c, f) x_(c, f) \

"s.t": &sum_(c=1)^C x_(c,f) = 1 quad forall f in FF \

&x_(c, f) in {0, 1} quad forall f in {1,..., F}, c in CC
$

This is trivially solvable by selecting $x_(c', f) = 1$ for the $c'$ that haves
$c_(c', f) = limits(max)_(c in CC) c_(c, f)$ for all $f in FF$.

== Adding emission constraints

We introduce an emission value per field/crop choice denoted by $e_(c, f)$ and a
hyperparameter $E in NN$ to our optimization problem. $E$ describes the maximum
amount of emission we allow over across all fields. This extends the problem to:

$
max_x &sum_(f=1)^F sum_(c=1)^C p_(c, f) x_(c, f) \

"s.t": &sum_(c=1)^C x_(c, f) = 1 quad forall f in FF \

&sum_(f=1)^F sum_(c=1)^C e_(c,f) x_(c,f) <= E \

&x_(c, f) in {0, 1} quad forall f in FF, c in CC
$

Assuming this new constraint is violated in the optimal solution from before,
this increases the complexity of the problem. However as the added constraint is
linear we can still use modern ILP solvers to find near-optimal solutions in a
reasonable time.

== Further constraints

We have added a bunch of similar constraints such as
ensuring a minimum value of the total #emph[nature value] of the fields and
other linear constraints. They follow the same pattern as the emission
constraint, and beside adding a bit of complexity to the solution space, they do
not change the nature or type of optimization problem.

= Extending the problem to multiple years

A big complexity in this project is planning multiple year ahead, because we
want to model the fact that emission and yield for a given choice depends on the
previous choice of crop.

We define $Y in NN$ as the amount of years we want to plan and $YY$ as the set
of all years.

There are multiple ways this can be modelled.

== Linear modelling using transition decision variables <lin>

The first approach we tried was to introduce boolean decision variables for each
field, year and crop transition possibility. Let $x_(y, grave(c), c, f)$ denote
the decision if we in year $y$ plant crop $c$ when the previous year we planted
crop $grave(c)$ on field $f$. We assume $x_(0, grave(c), c, f)$ is known as a
starting decision for all fields. Furthermore we define $p$ and $e$ with similar
subscripts so $p_(grave(c), c, f)$ is the profit of planting crop $c$ on field
$f$ given that it last crop was $grave(c)$

We can then formulate the problem as

$
max_x &sum_(f=1)^F sum_(y=1)^Y sum_(c=1)^C sum_(grave(c)=1)^C
p_(grave(c), c, f) x_(y, grave(c), c, f) \

"s.t": &sum_(c=1)^C sum_(grave(c)=1)^C x_(y, grave(c), c, f) = 1
quad forall f in FF, y in YY \

&sum_(f=1)^F sum_(y=1)^Y sum_(c=1)^C sum_(grave(c)=1)^C
e_(grave(c), c, f) x_(y, grave(c), c, f) <= E \

&sum_(c=1)^C x_(y, grave(c), c, f) <= sum_(c=1)^C x_(y-1,c, grave(c), f) quad
forall f in FF, y in YY, grave(c) in CC \

&x_(y, grave(c), c, f) in {0, 1}
quad forall f in FF, c in CC, grave(c) in CC, y in YY
$

This approach keeps the problem as an ILP, but the solution space is now $FF
times CC times CC times YY$, and introduces $|FF| dot |YY| dot |CC|$ new
constraints, which for our use case makes the problem computationally
unreasonable to solve.

== Quadratic optimization formulation

Alternatively we can formulate the decision variables as $x_(y, c, f)$ and
modify the objective function as

$
max_x &sum_(f=1)^F sum_(y=1)^Y sum_(c=1)^C sum_(grave(c)=1)^C
p_(grave(c), c, f) x_(y-1, grave(c), f) x_(y, c, f) \

"s.t": &sum_(c=1)^C  x_(y, c, f) = 1 quad forall f in FF, y in YY \

&sum_(f=1)^F sum_(y=1)^Y sum_(c=1)^C sum_(grave(c)=1)^C
e_(grave(c), c, f) x_(y-1, grave(c), f) x_(y, c, f) <= E \

&x_(y, grave(c), c, f) in {0, 1} quad forall f in FF, c in CC, grave(c) in CC, y
in YY
$

This can also be rewriten to a quadratic form matrix optimization problem,
however the problem now has quadratic constraints and objective, and is not
guareenteed to be convex, so solving this is even more infeasible. We can note
that the first problem archives its linear formulation by introducing the
auxilary variables equal to the product of $x_(y-1,grave(c), f)$ and $x_(y,c,f)$

== Restricting the solution space

Going back to #ref(<lin>) we can study the problem of the vast solution space.
If  we can define a reasonable set of valid crop rotations that can be chosen
for each field we restrict the solution space a lot. Denote the set of all valid
crop rotations over a period of Y years as $VV$. If we restrict that $|VV|
<< |CC| dot |CC| dot |YY|$ we are back to the initial problem in
#ref(<initial>) with $CC$ substituted with $VV$, which as long as $VV$ is of
reasonable low cardinality we are able to find near-optimal solutions using
modern solvers.
