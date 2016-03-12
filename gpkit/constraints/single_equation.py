"Implements SingleEquationConstraint"
from abc import ABCMeta, abstractproperty, abstractmethod
from operator import le, ge, eq
from ..small_scripts import try_str_without
from ..repr_conventions import _str, _repr, _repr_latex_


class SingleEquationConstraint:
    "Constraint expressible in a single equation."
    latex_opers = {"<=": "\\leq", ">=": "\\geq", "=": "="}
    func_opers = {"<=": le, ">=": ge, "=": eq}

    __metaclass__ = ABCMeta

    __str__ = _str
    __repr__ = _repr
    _repr_latex_ = _repr_latex_

    @abstractproperty
    def left(self):
        pass

    @abstractproperty
    def right(self):
        pass

    @abstractproperty
    def oper(self):
        pass

    @abstractmethod
    def str_without(self, excluded=None):
        if excluded is None:
            excluded = ["units"]
        return "%s %s %s" % (try_str_without(self.left, excluded),
                             self.oper,
                             try_str_without(self.right, excluded))

    @abstractmethod
    def subconstr_str(self, excluded):
        "The collapsed string of a constraint"
        pass

    @abstractmethod
    def subconstr_latex(self, excluded):
        "The collapsed latex of a constraint"
        pass

    @abstractmethod
    def latex(self, excluded=None):
        if not excluded:
            excluded = ["units"]  # previously bool(self.left.units)
        latex_oper = self.latex_opers[self.oper]
        return ("%s %s %s" % (self.left.latex(excluded), latex_oper,
                              self.right.latex(excluded)))

    def sub(self, subs, value=None):
        "Returns a substituted version of this constraint."
        if value:
            subs = {subs: value}
        subbed = self.func_opers[self.oper](self.left.sub(subs),
                                            self.right.sub(subs))
        subbed.substitutions = self.substitutions
        return subbed

    def process_result(self, result):
        "Process solver results"
        pass
