#!/usr/bin/perl
use lib '..';
use CGI qw/:standard/;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;

# form for entering patron barcodes to delete
