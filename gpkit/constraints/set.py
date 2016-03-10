"Implements ConstraintSet"
from ..small_classes import HashVector, KeySet, KeyDict
from ..small_scripts import try_str_without


class ConstraintSet(list):
    "Recursive container for ConstraintSets and Inequalities"
    def __init__(self, constraints, substitutions=None):
        list.__init__(self, constraints)
        subs = substitutions if substitutions else {}
        if hasattr(self, "cost"):
            subs.update(self.cost.values)
        if not isinstance(constraints, ConstraintSet):
            # constraintsetify everything
            for i, constraint in enumerate(self):
                if (hasattr(constraint, "__iter__") and
                        not isinstance(constraint, ConstraintSet)):
                    self[i] = ConstraintSet(constraint)
        else:
            # grab the substitutions dict from the top constraintset
            subs.update(constraints.substitutions)
        self.substitutions = KeyDict.with_keys(self.varkeys,
                                               self._iter_subs(subs))

    def str_without(self, excluded=[]):
        return "[" + ", ".join([try_str_without(el, excluded)
                                for el in self]) + "]"

    def __str__(self):
        "Returns list-like string, but with str(el) instead of repr(el)."
        return self.str_without()

    def __repr__(self):
        return "gpkit.%s(%s)" % (self.__class__.__name__, self)

    def latex(self):
        return ("\\begin{bmatrix}" +
                " \\\\\n".join(el.latex() for el in self) +
                "\\end{bmatrix}")

    def _repr_latex_(self):
        return "$$"+self.latex()+"$$"

    def flat(self, constraintsets=True):
        "Yields contained constraints, optionally including constraintsets."
        for constraint in self:
            if not isinstance(constraint, ConstraintSet):
                yield constraint
            else:
                if constraintsets:
                    yield constraint
                subgenerator = constraint.flat(constraintsets)
                for yielded_constraint in subgenerator:
                    yield yielded_constraint

    def sub(self, subs, value=None):
        "Substitutes in place."
        if hasattr(self, "cost"):
            self.cost = self.cost.sub(subs, value)
        for i, constraint in enumerate(self):
            self[i] = constraint.sub(subs, value)
        return self

    @property
    def varkeys(self):
        "Varkeys present in the constraints"
        out = KeySet()
        if hasattr(self, "cost"):
            out.update(self.cost.varkeys)
        for constraint in self:
            if hasattr(constraint, "varkeys"):
                out.update(constraint.varkeys)
        return out

    def as_posyslt1(self):
        "Returns list of posynomials which must be kept <= 1"
        posylist, self.posymap = [], []
        for constraint in self:
            constraint.substitutions = KeyDict()
            constraint.substitutions.update(self.substitutions)
            posys = constraint.as_posyslt1()
            self.posymap.append(len(posys))
            posylist.extend(posys)
        return posylist

    def sens_from_dual(self, p_senss, m_sensss):
        """Computes constraint and variable sensitivities from dual solution

        Arguments
        ---------
        p_senss : list
            Sensitivity of each posynomial returned by `self.as_posyslt1()`

        m_sensss: list of lists
            Each posynomial's monomial sensitivities


        Returns
        -------
        constraint_sens : dict
            The interesting and computable sensitivities of this constraint

        var_senss : dict
            The variable sensitivities of this constraint
        """
        constr_sens = {}
        var_senss = HashVector()
        offset = 0
        for i, constr in enumerate(self):
            n_posys = self.posymap[i]
            p_ss = p_senss[offset:offset+n_posys]
            m_sss = m_sensss[offset:offset+n_posys]
            constr_sens[str(constr)], v_ss = constr.sens_from_dual(p_ss, m_sss)
            var_senss += v_ss
            offset += n_posys
        return constr_sens, var_senss

    def as_gpconstr(self, x0):
        """Returns GPConstraint approximating this constraint at x0

        When x0 is none, may return a default guess."""
        cs = ConstraintSet([constr.as_gpconstr(x0) for constr in self])
        cs.substitutions.update(self.substitutions)
        return cs

    def sens_from_gpconstr(self, gpapprox, gp_sens, var_senss):
        """Computes sensitivities from GPConstraint approximation

        Arguments
        ---------
        gpapprox : GPConstraint
            The GPConstraint returned by `self.as_gpconstr()`

        gpconstr_sens :
            Sensitivities created by `gpconstr.sens_from_dual`

        var_senss : dict
            Variable sensitivities from last GP solve.


        Returns
        -------
        constraint_sens : dict
            The interesting and computable sensitivities of this constraint
        """
        constr_sens = {}
        for i, c in enumerate(self):
            gpa = gpapprox[i]
            gp_s = gp_sens[str(gpa)]
            constr_sens[str(c)] = c.sens_from_gpconstr(gpa, gp_s, var_senss)
        return constr_sens

    def process_result(self, result):
        """Does arbitrary computation / manipulation of a program's result

        There's no guarantee what order different constraints will process
        results in, so any changes made to the program's result should be
        careful not to step on other constraint's toes.

        Potential Uses
        --------------
          - check that an inequality was tight
          - add values computed from solved variables

        """
        processed = {}
        for constraint in self:
            if hasattr(constraint, "process_result"):
                p = constraint.process_result(result)
                if p:
                    processed.update(p)
        return processed

    def _iter_subs(self, substitutions):
        for constraint in self.flat():
            if hasattr(constraint, "substitutions"):
                subs = constraint.substitutions
                constraint.substitutions = {}
                yield subs
        yield substitutions