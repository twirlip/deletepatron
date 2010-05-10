#!/usr/bin/perl
package Sitka::Session;
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
#use CGI::Session qw/-ip-match/;
use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;
use File::Spec;
use DateTime;
use OpenSRF::Utils::Cache;

my $prefix = "DELETEPATRON"; # Prefix for caching values
my $cache;
my $cache_timeout = 300;

our @fail;

sub new {
  my $class = shift;
  my $self = {};
  bless $self, $class;
  $self->{type} = undef;
  $self->{authenticated} = undef;
  $self->{ou} = undef;
  $self->{staff} = undef;
  $self->{cannot_delete} = undef;
  $self->{patrons} = undef;
  $self->{not_found} = undef;
  $self->{invalid} = undef;
  return $self;
}

sub initialize_session {
  my $self = shift;
  my $usr = shift;

  # set up a memcached session for subsequent use
  $cache = OpenSRF::Utils::Cache->new('global');
  my $ckey = "$prefix-$usr-" . DateTime->now;
  $cache->put_cache($ckey, \$self, $cache_timeout);
  return;
}

sub retrieve_session {
  my $ckey = shift;
  my $cached_session = $cache->get_cache($ckey) || undef;
  if ($cached_session) {
    # TODO: this is ugly and can surely be done more elegantly
    $self->{type} = $cached_session->{type};
    $self->{authenticated} = $cached_session->{authenticated};
    $self->{ou} = $cached_session->{ou};
    $self->{staff} = $cached_session->{staff};
    $self->{cannot_delete} = $cached_session->{cannot_delete};
    $self->{patrons} = $cached_session->{patrons};
    $self->{not_found} = $cached_session->{not_found};
    $self->{invalid} = $cached_session->{invalid};
  }
  return;
}

sub authenticate {
  my ($self, $usr, $pwd) = @_;
  my $has_perms = undef; # unset unless user has DELETE_USER permissions
  my $usrdata = check_password($usr, $pwd);
  if ($usrdata) {
    $has_perms = check_perms($usrdata->{usr_id}, $usrdata->{home_ou});
  }
  if ($has_perms) {
    # user is authenticated!
    $self->initialize_session($usr);
    $self->{authenticated} = 1;
    $self->{ou} = $usrdata->{home_ou};
    $self->{staff} = $usrdata;
  } 
  $self->{fail} = \@fail;
  return; 
}

sub check_password {
  my ($usr, $pwd) = @_; # no $self param here, and yet it's needed by check_perms() ... I don't get it.

  # TODO: do this via OpenSRF API rather than direct DB lookup
  my $db = Sitka::DB->connect();
  my $usrdata = $db->{dbh}->selectrow_hashref("SELECT id as usr_id, usrname, passwd, home_ou FROM actor.usr WHERE usrname = ? and passwd = md5(?);", undef, ($usr, $pwd));
  if ($usrdata) {
    return $usrdata;
  } else {
    push @fail, { error => "INVALID_LOGIN: username = $usr, password = $pwd" };
    return;
  }
}

sub check_perms {
  my ($usr_id, $home_ou) = @_;
  #my ($self, $usr_id, $home_ou) = @_; # Perl 5.10 (or EG 1.6) seems to want $self as a param here, 5.8 (or EG 1.2) does not

  # make sure this user has permission to delete users
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'DELETE_USER');
  if ($p) {
    push @fail, { error => 'MISSING_PERMS: ' . $p->{textcode} . ": " . $p->{desc} };
    return;
  } else {
    return 1;
  }
}

# What type of session is this? (e.g. delete patrons, delete cards only)
# Possible values:
#   DELETE_PATRON (default)
#   DELETE_CARD
#   UNDELETE_PATRON
sub type {
  my $self = shift;
  my $type = shift || 'DELETE_PATRON';
  $self->{session_type} = $type unless defined $self->{session_type};
  return $self->{session_type};
}

# TODO: write a proper messaging system in Sitka.pm to handle fail() msgs
sub fail {
  print $cgi->header,
        $cgi->start_html('Error'),
        $cgi->h1('Error');
  foreach $failmsg (@fail) {
    my ($msgtype, $msgtext) = each %{$failmsg};
    print $cgi->p("$msgtype : $msgtext");
  }
  print $cgi->end_html;
  exit;
}

sub login {
  my $msgs = shift;
  my $cgi = CGI->new;
  print $cgi->header,
        $cgi->start_html( -title => 'Sitka Patron Deletions - Login',
                          -style => { -src => "../style.css" },
                        ),
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
