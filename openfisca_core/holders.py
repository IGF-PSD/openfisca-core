# -*- coding: utf-8 -*-


from __future__ import division

import numpy as np

from . import periods
from .commons import empty_clone
from .columns import MONTH, YEAR, PERMANENT


class DatedHolder(object):
    """A wrapper of the value of a variable for a given period (and possibly a given set of extra parameters).
    """
    holder = None
    period = None
    extra_params = None

    def __init__(self, holder, period, value, extra_params = None):
        self.holder = holder
        self.period = period
        self.extra_params = extra_params
        self.value = value

    @property
    def array(self):
        return self.value

    @array.setter
    def array(self, array):
        raise ValueError('Impossible to modify DatedHolder.array. Please use Holder.put_in_cache.')

    @property
    def column(self):
        return self.holder.column

    @property
    def entity(self):
        return self.holder.entity

    def to_value_json(self, use_label = False):
        transform_dated_value_to_json = self.holder.column.transform_dated_value_to_json
        return [
            transform_dated_value_to_json(cell, use_label = use_label)
            for cell in self.array.tolist()
            ]


class Holder(object):
    _array = None  # Only used when column.is_permanent
    _array_by_period = None  # Only used when not column.is_permanent
    column = None
    entity = None
    formula = None
    formula_output_period_by_requested_period = None

    def __init__(self, simulation, column = None):
        assert column is not None
        assert self.column is None
        self.column = column
        self.simulation = simulation
        self.entity = self.simulation.entities[self.column.entity.key]

    @property
    def array(self):
        if not self.column.is_permanent:
            return self.get_array(self.simulation.period)
        return self._array

    @array.setter
    def array(self, array):
        if not self.column.is_permanent:
            return self.put_in_cache(array, self.simulation.period)
        if self.simulation.debug or self.simulation.trace:
            variable_infos = (self.column.name, None)
            step = self.simulation.traceback.get(variable_infos)
            if step is None:
                self.simulation.traceback[variable_infos] = dict(
                    holder = self,
                    )
        self._array = array

    def calculate(self, period = None, **parameters):
        dated_holder = self.compute(period = period, **parameters)
        return dated_holder.array

    def calculate_output(self, period):
        return self.formula.calculate_output(period)

    def clone(self):
        """Copy the holder just enough to be able to run a new simulation without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key in ('_array_by_period',):
                if value is not None:
                    # There is no need to copy the arrays, because the formulas don't modify them.
                    new_dict[key] = value.copy()
            elif key not in ('entity', 'formula'):
                new_dict[key] = value

        new_dict['entity'] = self.entity
        # Caution: formula must be cloned after the entity has been set into new.
        formula = self.formula
        if formula is not None:
            new_dict['formula'] = formula.clone(new)

        return new

    def compute(self, period = None, **parameters):
        """Compute array if needed and return a dated holder containing it.

        The returned dated holder is always of the requested period and this method never returns None.
        """
        if period is None:
            period = self.simulation.period
        column = self.column

        # Check that the requested period matches period_behavior
        if not self.column.period_behavior == PERMANENT:
            if ((self.column.period_behavior == MONTH and period.unit != periods.MONTH) or
                    (self.column.period_behavior == YEAR and period.unit != periods.YEAR)):
                raise ValueError('Computation requested with wrong period unit for variable {} ({} instead of {})'.format(
                    self.column.name,
                    period.unit, self.column.period_behavior))
        if period.size != 1:
            raise ValueError('Computation requested for complex period {} for variable {}'.format(
                period, self.column.name))

        # First look for a value already cached
        dated_holder = self.get_from_cache(period, parameters.get('extra_params'))
        if dated_holder.array is not None:
            return dated_holder
        assert self._array is None  # self._array should always be None when dated_holder.array is None.

        # Request a computation
        column_start_instant = periods.instant(column.start)
        column_stop_instant = periods.instant(column.end)
        if (column_start_instant is None or column_start_instant <= period.start) \
                and (column_stop_instant is None or period.start <= column_stop_instant):
            formula_dated_holder = self.formula.compute(period = period, **parameters)
            assert formula_dated_holder is not None
            if not column.is_permanent:
                assert formula_dated_holder.period == period, \
                    "Requested period {} differs from {} returned by variable {}".format(period,
                        formula_dated_holder.period, column.name)
            return formula_dated_holder
        array = self.default_array()
        return self.put_in_cache(array, period)

    def compute_add(self, period = None, **parameters):
        # Check that the requested period matches period_behavior
        if self.column.period_behavior == YEAR and period.unit == periods.MONTH:
            raise ValueError('Computation on period {} impossible on yearly variable {}'.format(
                period, self.column.name
                ))

        if self.column.period_behavior == MONTH:
            variable_period_unit = periods.MONTH
        elif self.column.period_behavior == YEAR:
            variable_period_unit = periods.YEAR
        else:
            ValueError('compute_add can be used only for yearly or monthly variables.')

        after_instant = period.start.offset(period.size, period.unit)
        sub_period = period.start.period(variable_period_unit)
        array = None
        while sub_period.start < after_instant:
            dated_holder = self.compute(period = sub_period, **parameters)
            if array is None:
                array = dated_holder.array.copy()
            else:
                array += dated_holder.array
            sub_period = sub_period.offset(1)

        return DatedHolder(self, period, array, parameters.get('extra_params'))

    '''
    def compute_add_divide(self, period = None, **parameters):
        dated_holder = self.get_from_cache(period, parameters.get('extra_params'))
        if dated_holder.array is not None:
            return dated_holder

        array = None
        unit = period.unit
        if unit == u'month':
            remaining_period_months = period.size
        else:
            assert unit == u'year', unit
            remaining_period_months = period.size * 12
        requested_period = period.start.period(unit)
        # We expect the compute calls to return a period different than the requested one.
        parameters['accept_other_period'] = True
        while True:
            dated_holder = self.compute(period = requested_period, **parameters)
            requested_start = requested_period.start
            returned_period = dated_holder.period
            returned_start = returned_period.start
            assert returned_start.day == 1
            # Note: A dated formula may start after requested period.
            # assert returned_start <= requested_start <= returned_period.stop, \
            #     "Period {} returned by variable {} doesn't include start of requested period {}.".format(
            #         returned_period, self.column.name, requested_period)
            requested_start_months = requested_start.year * 12 + requested_start.month
            returned_start_months = returned_start.year * 12 + returned_start.month
            if returned_period.unit == u'month':
                intersection_months = min(requested_start_months + requested_period.size,
                    returned_start_months + returned_period.size) - requested_start_months
                intersection_array = dated_holder.array * intersection_months / returned_period.size
            else:
                assert returned_period.unit == u'year', \
                    "Requested a monthly or yearly period. Got {} returned by variable {}.".format(
                        returned_period, self.column.name)
                intersection_months = min(requested_start_months + requested_period.size,
                    returned_start_months + returned_period.size * 12) - requested_start_months
                intersection_array = dated_holder.array * intersection_months / (returned_period.size * 12)
            if array is None:
                array = intersection_array.copy()
            else:
                array += intersection_array

            remaining_period_months -= intersection_months
            if remaining_period_months <= 0:
                return self.put_in_cache(array, period, parameters.get('extra_params'))
            if remaining_period_months % 12 == 0:
                requested_period = requested_start.offset(intersection_months, u'month').period(u'year')
            else:
                requested_period = requested_start.offset(intersection_months, u'month').period(u'month')
    '''

    def compute_divide(self, period = None, **parameters):
        # Check that the requested period matches period_behavior
        if self.column.period_behavior != YEAR:
            raise ValueError('Holder.compute_divide must be used on yearly variables. This is not the case for {}'.format(
                self.column.name
                ))
        if period.unit != periods.MONTH:
            raise ValueError('Holder.compute_divide must be used on a month. This is not the case for {}'.format(
                period
                ))

        computation_period = period.this_year
        dated_holder = self.compute(period = computation_period, **parameters)
        array = dated_holder.array / 12.
        return DatedHolder(self, period, array, parameters.get('extra_params'))

    def delete_arrays(self):
        if self._array is not None:
            del self._array
        if self._array_by_period is not None:
            del self._array_by_period

    def get_array(self, period, extra_params = None):
        if self.column.is_permanent:
            return self.array
        assert period is not None
        array_by_period = self._array_by_period
        if array_by_period is not None:
            values = array_by_period.get(period)
            if values is not None:
                if extra_params:
                    return values.get(tuple(extra_params))
                else:
                    if(type(values) == dict):
                        return values.values()[0]
                    return values
        return None

    def graph(self, edges, get_input_variables_and_parameters, nodes, visited):
        column = self.column
        if self in visited:
            return
        visited.add(self)
        nodes.append(dict(
            id = column.name,
            group = self.entity.key,
            label = column.name,
            title = column.label,
            ))
        period = self.simulation.period
        formula = self.formula
        if formula is None or column.start is not None and column.start > period.stop.date or column.end is not None \
                and column.end < period.start.date:
            return
        formula.graph_parameters(edges, get_input_variables_and_parameters, nodes, visited)

    @property
    def real_formula(self):
        formula = self.formula
        if formula is None:
            return None
        return formula.real_formula

    def set_input(self, period, array, behavior=None):
        self.formula.set_input(period, array, behavior=behavior)

    def put_in_cache(self, value, period, extra_params = None):
        simulation = self.simulation

        if not self.column.period_behavior == PERMANENT:
            assert periods is not None
            if ((self.column.period_behavior == MONTH and period.unit != periods.MONTH) or
               (self.column.period_behavior == YEAR and period.unit != periods.YEAR)):
                raise ValueError('Wrong period unit during cache write for variable {} ({} instead of {})'.format(
                    self.column.name,
                    period.unit, self.column.period_behavior))

        if (simulation.opt_out_cache and
                simulation.tax_benefit_system.cache_blacklist and
                self.column.name in simulation.tax_benefit_system.cache_blacklist):
            return DatedHolder(self, period, value, extra_params)

        if self.column.is_permanent:
            self.array = value

        if simulation.debug or simulation.trace:
            variable_infos = (self.column.name, period)
            step = simulation.traceback.get(variable_infos)
            if step is None:
                simulation.traceback[variable_infos] = dict(
                    holder = self,
                    )
        array_by_period = self._array_by_period
        if array_by_period is None:
            self._array_by_period = array_by_period = {}
        if extra_params is None:
            array_by_period[period] = value
        else:
            if array_by_period.get(period) is None:
                array_by_period[period] = {}
            array_by_period[period][tuple(extra_params)] = value
        return self.get_from_cache(period, extra_params)

    def get_from_cache(self, period, extra_params = None):
        if self.column.is_permanent:
            return self

        value = self.get_array(period, extra_params)
        return DatedHolder(self, period, value, extra_params)

    def get_extra_param_names(self, period):
        from .formulas import DatedFormula
        if isinstance(self.formula, DatedFormula):
            # Get the function that matches the period
            formula = [
                formula for formula in self.formula.dated_formulas
                if (not formula['start_instant'] or formula['start_instant'] < period.stop) and (not formula['stop_instant'] or formula['stop_instant'] > period.start)
                ][0]['formula'].function
        else:
            formula = self.formula.function

        return formula.__func__.func_code.co_varnames[3:]

    def to_value_json(self, use_label = False):
        column = self.column
        transform_dated_value_to_json = column.transform_dated_value_to_json

        def extra_params_to_json_key(extra_params, period):
            return '{' + ', '.join(
                ['{}: {}'.format(name, value)
                    for name, value in zip(self.get_extra_param_names(period), extra_params)]
                ) + '}'

        if column.is_permanent:
            array = self._array
            if array is None:
                return None
            return [
                transform_dated_value_to_json(cell, use_label = use_label)
                for cell in array.tolist()
                ]
        value_json = {}
        if self._array_by_period is not None:
            for period, array_or_dict in self._array_by_period.iteritems():
                if type(array_or_dict) == dict:
                    value_json[str(period)] = values_dict = {}
                    for extra_params, array in array_or_dict.iteritems():
                        extra_params_key = extra_params_to_json_key(extra_params, period)
                        values_dict[str(extra_params_key)] = [
                            transform_dated_value_to_json(cell, use_label = use_label)
                            for cell in array.tolist()
                            ]
                else:
                    value_json[str(period)] = [
                        transform_dated_value_to_json(cell, use_label = use_label)
                        for cell in array_or_dict.tolist()
                        ]
        return value_json

    def default_array(self):
        array_size = self.entity.count
        array = np.empty(array_size, dtype = self.column.dtype)
        array.fill(self.column.default)
        return array
