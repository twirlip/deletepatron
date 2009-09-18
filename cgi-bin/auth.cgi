#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use lib '..';
use lib '/openils/lib/perl5/';
use CGI;
use CGI::Session qw/-ip-match/;
use Sitka::DB;
use Sitka::Session;
#use OpenSRF::System;
#use OpenILS::Application::AppUtils;
#use Data::Dumper;

$cgi = new CGI;

@fail = ();
push @fail, 'MISSING_PARAMS' unless ($cgi->param('usr') && $cgi->param('pwd'));

my $usr = $cgi->param('usr');
my $pwd = $cgi->param('pwd');

my $session = authenticate($usr, $pwd);
login() unless ($session);
$cookie = $cgi->cookie(CGISESSID => $session->id);

print $cgi->header( -cookie=>$cookie );
print $cgi->start_html('Authenticated!'),
      $cgi->h1('User has been authenticated.'),
      $cgi->end_html;

