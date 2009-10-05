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

our @fail;

sub new {
  my $usr = shift;
  my $pwd = shift;
  if (authenticate($usr, $pwd)) {
    # TODO: user is authenticated; create CGI session
  } else {
    login(\@fail);
  }
}

sub authenticate {
  my $usr = shift;
  my $pwd = shift;
  my $has_perms = undef; # unset unless user has DELETE_USER permissions
  my $usrdata = check_password($usr, $pwd);
  if ($usrdata) {
    $has_perms = check_perms($usrdata->{usr_id}, $usrdata->{home_ou});
  }
  if ($has_perms) {
    # user is authenticated!
    # TODO: return a list of OUIDs for which user has permission to delete users
    return $usrdata;
  } 
  return;
}

sub check_password {
  my ($usr, $pwd) = @_;

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->selectrow_hashref("SELECT id, usrname, passwd, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    return $usrdata;
  } else {
    push @fail, 'INVALID_LOGIN';
    return;
  }
}

sub check_perms {
  my ($usr_id, $home_ou) = @_;

  # make sure this user has permission to delete users
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'DELETE_USER');
  if ($p) {
    push @fail, 'MISSING_PERMS: ' . $p->{textcode} . ": " . $p->{desc};
    return;
  } else {
    return 1;
  }
}

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
  my $cgi = CGI->new;
  print $cgi->header,
        $cgi->start_html('Sitka Patron Deletions - Login'),
        $cgi->h1('Please Login');
  foreach my $msg (@{$msgs}) {
    while (my ($msgtype, $msgtext) = each %{$msg}) {
      print $cgi->div({-class=>$msgtype},$msgtext);
    }
  }
  print $cgi->start_form( -method=>'POST', -action=>"input.cgi" );
  print $cgi->textfield('usr'),
        $cgi->password_field('pwd'),
        $cgi->submit('submit','Login');
  print $cgi->end_form();
  print $cgi->end_html();
  exit;
}

1; # perl is stupid.
