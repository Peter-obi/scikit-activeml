import numpy as np

from .base import BudgetManager


class FixedBudget(BudgetManager):
    """Budget manager which checks, whether the specified budget has been
    exhausted already. If not, an instance is sampled, when the utility is
    higher than the specified budget.

    This budget manager counts the number of already observed instances and
    compares that to the number of sampled instances. If the ratio is smaller
    than the specified budget, i.e.,
    n_observed_instances * budget - n_sampled_instances >= 1 , the budget
    manager samples an instance when its utility is higher than the budget.

    Parameters
    ----------
    budget : float
        Specifies the ratio of instances which are allowed to be sampled, with
        0 <= budget <= 1.
    """
    def __init__(self, budget):
        super().__init__(budget)
        self.observed_instances = 0
        self.sampled_instances = 0

    def is_budget_left(self):
        """Check whether there is any utility given to sample(...), which may
        lead to sampling the corresponding instance, i.e., check if sampling
        another instance is currently possible under the specified budgeting
        constraint. This function is useful to determine, whether a provided
        utility is not sufficient, or the budgeting constraint was simply
        exhausted. For this budget manager this function returns True, when
        n_observed_instances * budget  - n_sampled_instances >= 1.

        Returns
        -------
        budget_left : bool
            True, if there is a utility which leads to sampling another
            instance.
        """
        available_budget = (self.observed_instances * self.budget
                            - self.sampled_instances)
        return available_budget >= 1

    def sample(self, utilities, simulate=False, return_budget_left=False,
               **kwargs):
        """Ask the budget manager which utilities are sufficient to sample the
        corresponding instance.

        Parameters
        ----------
        utilities : ndarray of shape (n_samples,)
            The utilities provided by the stream-based active learning
            strategy, which are used to determine whether sampling an instance
            is worth it given the budgeting constraint.

        return_utilities : bool, optional
            If true, also return whether there was budget left for each
            assessed utility. The default is False.

        simulate : bool, optional
            If True, the internal state of the budget manager before and after
            the query is the same. This should only be used to prevent the
            budget manager from adapting itself. The default is False.

        Returns
        -------
        sampled_indices : ndarray of shape (n_sampled_instances,)
            The indices of instances represented by utilities which should be
            sampled, with 0 <= n_sampled_instances <= n_samples.

        budget_left: ndarray of shape (n_samples,), optional
            Shows whether there was budget left for each assessed utility. Only
            provided if return_utilities is True.
        """
        # keep record if the instance is sampled and if there was budget left,
        # when assessing the corresponding utilities
        sampled = np.full(len(utilities), False)
        budget_left = np.full(len(utilities), False)

        # keep the internal state to reset it later if simulate is true
        init_observed_instances = self.observed_instances
        init_sampled_instances = self.sampled_instances

        # check for each sample separately if budget is left and the utility is
        # high enough
        for i, utility in enumerate(utilities):
            self.observed_instances += 1
            budget_left[i] = self.is_budget_left()
            sampled[i] = budget_left[i] and (utility >= 1 - self.budget)
            self.sampled_instances += sampled[i]

        # set the internal state to the previous values
        if simulate:
            self.observed_instances = init_observed_instances
            self.sampled_instances = init_sampled_instances

        # get the indices instances that should be sampled
        sampled_indices = np.where(sampled)[0]

        # check if budget_left should be returned
        if return_budget_left:
            return sampled_indices, budget_left
        else:
            return sampled_indices
