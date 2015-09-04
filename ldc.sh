#!/bin/bash
###################################################################################################
#    System:  CVG
#    Module:  LDC
# $Workfile:   ldc.sh $
#     $Date:   2011-11-01 18:48:32 GMT $
# $Revision:   \main\CVG_TLDC_Integration\3 $
####################################################################################################
# CONFIDENTIAL. All rights reserved. Thales Rail Signalling Solutions. This computer program is
# protected under Copyright. Recipient is to retain the program in confidence, and is not permitted
# to copy, use, distribute, modify or translate the program without authorization.
###################################################################################################
# Used in the lab to start data collector
# Usage ./ldc.sh [ target ] [ -- extra_args ]
# The extra_args appear after -- and will be passed to ./lodacol.py

#
# Examples:
#
# Basic Usage
# ---------------------------------------------
# Collect all variables listed in *.var files from current directory
# from vobc replica 2 
#    #./ldc.sh vobc2
#
#
# Advanced Usage
# ---------------------------------------------
# Extract all variables listed in atp_generic.var from replica with ip 192.168.200.3
#    #./ldc.sh -- -t 192.168.200.3 atp_generic.var
#
#
###################################################################################################

#set -x

{ pushd $(dirname $0); } 1>/dev/null
THIS_DIR=$(pwd)
{ popd; } 1>/dev/null

TARGET=

function die()
{
    echo "FAILED: $1" >&2
    exit 1
}

function run_python()
{
    local vpython
    for p in "/usr/bin/python" "/opt/python27/bin/python"; do
	while read vMajor vMinor ; do
	    if [ x"$vMajor" = "x2" ] && [ $vMinor -ge 6 ]; then
		vpython=$p
	    fi
	done < <($p -c "import sys; print sys.version_info[0],sys.version_info[1]" 2>/dev/null)
    done

    [ x"$vpython" = x ] && die "Python version >=2.6 is needed"

    $vpython $@
}

function usage()
{
    echo "This script is a wrapper for lodacol.py"
    echo "USAGE ./ldc.sh [target] [-- extra_args]"
    echo "For lodacol.py"
    run_python $THIS_DIR/lodacol.py --help
}

while [ -n "$1" ]; do
    case $1 in
	-h|--help)
	    usage
	    exit 1
	    ;;
	--)
	    shift
	    break;
	    ;;
	
	*)
	    [ -n "$TARGET" ] && { usage; exit 1; }
	    TARGET=$1
	    shift
	    ;;
    esac
done

[ -n "$TARGET" ] && TARGET="-t $TARGET"

run_python $THIS_DIR/lodacol.py $TARGET $@

