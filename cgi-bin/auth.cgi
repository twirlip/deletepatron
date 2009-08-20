#!/usr/bin/perl
# a horribly hacked-together authentication mechanism for the Sitka deletepatron system
use lib '..';
use lib '/openils/lib/perl5/';
use CGI qw/:standard/;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;
use Data::Dumper;

$q = new CGI;

print header,
			start_html('Authentication'),
			h1('Authenticating...');

fail('Please login.') unless (param()); # TODO: write a messaging system to handle fail() msgs

if (param()) {
	my $usr = param('usr');
	my $pwd = param('pwd');
  my $usr_id;
  my $home_ou;

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT id, usrname, passwd, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    $usr_id  = $usrdata->{id};
    $home_ou = $usrdata->{home_ou};
  } else {
    print p("AUTHENTICATION FAIL!");
    exit;
  }

  # make sure this user has permission to delete users
  print p("User $usr (ID $usr_id, home library $home_ou) is authenticated.");
  print p("Checking for DELETE_USER permission...");
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'DELETE_USER');
  print pre(Dumper($p));
  if ($p) {
    print p($p->{textcode} . ": " . $p->{desc});
  } else {
    print p("Yep, you can delete users.\n");
  }

}

# TODO: Flag this session as authenticated, set $ou, and proceed to input.cgi

print p("All done!");
print end_html;

sub fail {
	my $msg = shift;
	print $q->h1('Error'),
				$q->p($msg),
				$q->end_html;
	exit;
}

