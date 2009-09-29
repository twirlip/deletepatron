#!/usr/bin/perl
package Sitka::Session;
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
use CGI::Session qw/-ip-match/;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;

sub new {
  my $usr = shift;
  my $pwd = shift;
  my $session = authenticate($usr, $pwd);
  login() unless ($session);
  return $session;
}

sub authenticate {
  my $usr = shift;
  my $pwd = shift;
  my $usr_id;
  my $home_ou;

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT id, usrname, passwd, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    $usr_id  = $usrdata->{id};
    $home_ou = $usrdata->{home_ou};
  } else {
    push @fail, 'INVALID_LOGIN';
    return;
  }

  # make sure this user has permission to delete users
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'DELETE_USER');
  if ($p) {
    push @fail, 'MISSING_PERMS: ' . $p->{textcode} . ": " . $p->{desc};
    return;
  }

  # user is authenticated!
  # TODO: return a list of OUIDs for which user has permission to delete users
  return $home_ou;
}

# TODO: write a proper messaging system in Sitka.pm to handle fail() msgs
sub fail {
  print $cgi->header,
        $cgi->start_html('Error'),
        $cgi->h1('Error');
  foreach $failmsg (@fail) {
    print $cgi->p($failmsg);
  }
  print $cgi->end_html;
  exit;
}

sub login {
  my $msgs = shift;
  my $destination = shift || undef;
  my $cgi = CGI->new;
  $destination = $cgi->script_name() if (!$destination);
  print $cgi->header,
        $cgi->start_html('Sitka Patron Deletions - Login'),
        $cgi->h1('Please Login');
  foreach my $msg (@{$msgs}) {
    while (my ($msgtype, $msgtext) = each %{$msg}) {
      print $cgi->div({-class=>$msgtype},$msgtext);
    }
  }
  print $cgi->start_form( -method=>'POST', -action=>$destination );
  print $cgi->textfield('usr'),
        $cgi->password_field('pwd'),
        $cgi->submit('submit','Login');
  print $cgi->end_form();
  print $cgi->end_html();
  exit;
}

1; # perl is stupid.
