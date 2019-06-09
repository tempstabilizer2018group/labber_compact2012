'''

'''
import itertools
from micropython_portable import *

def getValueFromDAC20(dac20_value):
    '''Assert gain=1.0'''
    assert isinstance(dac20_value, int)
    assert 0 <= dac20_value < DAC20_MAX
    value = VALUE_PLUS_MIN_MAX_V * 2.0 * dac20_value / DAC20_MAX - VALUE_PLUS_MIN_MAX_V
    return value

def getDAC30FromValue(value_plus_min_v):
    assert isinstance(value_plus_min_v, float)

    # scale to [0..DAC30_MAX-1]
    dac30_value = DAC30_MAX*(value_plus_min_v+VALUE_PLUS_MIN_MAX_V)/VALUE_PLUS_MIN_MAX_V/2.0
    dac30_value = int(dac30_value)
    # clip to [0..DAC30_MAX-1]
    dac30_value_clipped = min(max(dac30_value, 0), DAC30_MAX-1)

    assert isinstance(dac30_value_clipped, int)
    return dac30_value_clipped

def getDAC20DAC12IntFromValue(value_plus_min_v, calibrationLookup=None, iDac_index=0):
    '''
        Convert the desired voltage into a integer from [0..DAC30_MAX-1].

        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(-10.0)))
        ['0x00000', '0x00000']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(0.0)))
        ['0x80000', '0x00000']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(18.0e-6)))
        ['0x80000', '0x003C6']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(19.0e-6)))
        ['0x80000', '0x003FC']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(20.0e-6)))
        ['0x80001', '0x00031']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(5.0)))
        ['0xC0000', '0x00000']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(10.0)))
        ['0xFFFFF', '0x003FF']
        >>> list(map('0x{:05X}'.format, getDAC20DAC12IntFromValue(15.0)))
        ['0xFFFFF', '0x003FF']
    '''
    assert 0 <= iDac_index <= DACS_COUNT

    dac30_value = getDAC30FromValue(value_plus_min_v)
    dac20_value = dac30_value >> 10
    dac10_value = (dac30_value & 0x03FF)

    dac12_value = dac10_value
    if calibrationLookup is not None:
        # calibrationLookup(): This function returns a DAC12 offset for every 'dac20_value'.
        dac12_correctur = calibrationLookup(iDac_index, dac20_value)
        assert dac12_correctur < DAC12_MAX_CORRECTION_VALUE
        dac12_value += dac12_correctur
        assert 0 <= dac12_value < DAC12_MAX

    return dac20_value, dac12_value


def getDAC20DAC12HexStringFromValues(f_values_plus_min_v, calibrationLookup=None):
    '''
        Convert the desired voltage into a integer from [0..DAC30_MAX-1].

        >>> str_dac20, str_dac12 = getDAC20DAC12HexStringFromValues((-10.0, -5.0, -2.0, -1.0, 0.0, 1.0, 2.0, 5.0, 10.0, 15.0))
        >>> str_dac20
        '00000400006666673333800008CCCC99999C0000FFFFFFFFFF'
        >>> str_dac12
        '0000001990CC0003332660003FF3FF'
        >>> assert len(str_dac20) == DACS_COUNT*DAC20_NIBBLES
        >>> assert len(str_dac12) == DACS_COUNT*DAC12_NIBBLES
        >>> clear_dac_nibbles()
        >>> set_dac20_nibbles(str_dac20)
        >>> dac20_nibbles
        bytearray(b'1FFFFF1FFFFF1C000019999918CCCC180000173333166666140000100000')
        >>> set_dac12_nibbles(str_dac12)
        >>> dac12_nibbles
        bytearray(b'03FF3303FF3300003302663303333300003300CC33019933000033000033')

        >>> dac12_bytes_value1to9, dac12_bytes_value10 = splice_dac12(dac12_nibbles)
        >>> len(dac12_bytes_value1to9)
        27
        >>> len(dac12_bytes_value10)
        3
        >>> binascii.hexlify(dac12_bytes_value1to9)
        b'03ff3303ff3300003302663303333300003300cc33019933000033'
        >>> binascii.hexlify(dac12_bytes_value10)
        b'000033'
    '''
    assert len(f_values_plus_min_v) == DACS_COUNT

    list_i_dac20  = []
    list_i_dac12 = []
    for iDac_index, f_value_plus_min_v in zip(itertools.count(), f_values_plus_min_v):
        dac20_value, dac12_value = getDAC20DAC12IntFromValue(f_value_plus_min_v, calibrationLookup, iDac_index)
        list_i_dac20.append(dac20_value)
        list_i_dac12.append(dac12_value)

    str_dac20 = getHexStringFromListInt20(list_i_dac20)
    str_dac12 = getHexStringFromListInt12(list_i_dac12)

    assert len(str_dac20) == DACS_COUNT * DAC20_NIBBLES
    assert len(str_dac12) == DACS_COUNT * DAC12_NIBBLES

    return str_dac20, str_dac12

if __name__ == '__main__':
    import doctest
    doctest.testmod()

