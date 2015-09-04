#!/usr/bin/perl
###################################################################################################
#    System:  CVG
#    Module:  LDC
# $Workfile:   ldcsplit.pl $
#     $Date:   2011-10-17 21:46:42 GMT $
# $Revision:   \main\CVG_TLDC_Integration\1 $
####################################################################################################
# CONFIDENTIAL. All rights reserved. Thales Rail Signalling Solutions. This computer program is
# protected under Copyright. Recipient is to retain the program in confidence, and is not permitted
# to copy, use, distribute, modify or translate the program without authorization.
###################################################################################################
# Usage ./ldcsplit.pl input
# Takes a CSV file generated by ldc.sh (or lodacol.py) and splits it by application id.
# For each application id creates and output file with name APP_<ID>_<currentdate>.csv
###################################################################################################

use strict;

my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);

$year += 1900;
$mon += 1;

my $filesuffix = "_" . sprintf("%04d_%02d_%02d-%02d_%02d_%02d", ${year}, ${mon}, ${mday}, ${hour}, ${min}, ${sec});
$filesuffix .= ".csv";

my %openedfiles;

while (<>)
{
   my $line = $_;
   my $appid = -1;

   if ( $line =~ /AppId([0-9]+)/ ) {
      $appid = $1;
   }

   if ( $line =~ /([0-9]+)[,]/ ) {
      $appid = $1;
   }

   next if ($appid == -1);

   unless ( exists $openedfiles{$appid} ) {
	my $fn = "APP_${appid}" . $filesuffix ;
        print "Found appid=$appid creating output file $fn\n";
	open($openedfiles{$appid}, '>', $fn);
    }
    my $x = $openedfiles{$appid};
    print $x "$line";
   
}
