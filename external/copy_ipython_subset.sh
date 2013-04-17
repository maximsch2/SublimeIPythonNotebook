#!/bin/bash

IPYROOT=$1
IPYDIR=$IPYROOT/IPython

rm -rf nbformat
mkdir nbformat
cp $IPYROOT/COPYING.txt nbformat/

cp -R $IPYDIR/nbformat/v3/*.py nbformat/
rm -f nbformat/convert.py
rm -f nbformat/validator.py
sed -i bak "/convert/d" nbformat/__init__.py
cp $IPYDIR/utils/ipstruct.py nbformat/
cp $IPYDIR/utils/data.py nbformat/
cp $IPYDIR/utils/py3compat.py nbformat/
cp $IPYDIR/utils/encoding.py nbformat/
sed -i bak "s/IPython.utils//" nbformat/ipstruct.py
sed -i bak "s/IPython.utils//" nbformat/nbbase.py
sed -i bak "s/IPython.utils/./" nbformat/*.py
rm -f nbformat/*.pybak

