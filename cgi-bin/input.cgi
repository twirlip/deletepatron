#!/usr/bin/perl
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
#use CGI::Session qw/-ip-match/;
use Sitka::DB;
use Sitka::Session;
use OpenSRF::System;
use OpenILS::Application::AppUtils;

$cgi = CGI->new;

my $session = Sitka::Session->new($cgi->param('usr'), $cgi->param('pwd'));

print $cgi->header,
      $cgi->start_html('Hello World!'),
      $cgi->p('Session ID:',$session->id),
      $cgi->end_html;

# form for entering patron barcodes to delete
