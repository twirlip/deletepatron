#!/usr/bin/perl
package Sitka::Session;
use FindBin;
use lib "$FindBin::Bin/..";
use lib '/openils/lib/perl5/';
use CGI;
use Digest::MD5 qw/md5_hex/;
#use CGI::Session qw/-ip-match/;
#use Sitka::DB;
use OpenSRF::System;
use OpenILS::Application::AppUtils;
use OpenSRF::Utils::Logger qw/$logger/;
use File::Spec;
use DateTime;
use OpenSRF::Utils::Cache;
use Data::Dumper;

OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');

my $prefix = "DELETEPATRON"; # Prefix for caching values
my $cache_timeout = 300;

our @fail;

sub new {
  my $class = shift;
  my $self = {};
  bless $self, $class;
  $self->{ckey} = undef;
  $self->{type} = undef;
  $self->{authtoken} = undef;
  $self->{ou} = undef;
  $self->{staff} = undef;
  $self->{cannot_delete} = undef;
  $self->{usr_is_active} = undef;
  $self->{patrons} = undef;
  $self->{not_found} = undef;
  $self->{invalid} = undef;
  return $self;
}

sub initialize_session {
  my ($self, $usr) = @_;
  my $ckey = "$prefix-$usr-" . DateTime->now;
  $self->{ckey} = $ckey;
  $self->save_session();
  return;
}

sub save_session {
  my $self = shift;
  my $ckey = shift || $self->{ckey};
  my $cache = OpenSRF::Utils::Cache->new('global');
  $cache->delete_cache($ckey) if ($cache->get_cache($ckey));
  my $cache_href;
  foreach my $k (keys %$self) {
    $cache_href->{$k} = $self->{$k};
  }
  my @cache_content = ($cache_href);
  $cache->put_cache($ckey, \@cache_content, $cache_timeout);
}

sub retrieve_session {
  my ($self, $ckey) = @_;
  my $cache = OpenSRF::Utils::Cache->new('global');
  my $cache_content = $cache->get_cache($ckey) || undef;
  my $cached_session = shift @$cache_content;
  if ($cached_session) {
    foreach my $k (keys %$cached_session) {
      $self->{$k} = $cached_session->{$k};
    }
  } else {
    $logger->error("Could not retrieve cached session with key $ckey");
  }
  return;
}

sub authenticate {
  my ($self, $usr, $pwd) = @_;
  my $authtoken = oils_login($usr, $pwd);
  my $usrdata = $self->get_usrdata($usr);
  if ($usrdata) {
    my $has_perms = $self->check_perms($usrdata->{usr_id}, $usrdata->{home_ou});
    if ($has_perms) {
      $self->{authtoken} = $authtoken;
      $self->{ou} = $usrdata->{home_ou};
      $self->{staff} = $usrdata;
      $self->initialize_session($usr);
    } 
  }
  $self->{fail} = \@fail;
  $logger->info("user $usr is authenticated!");
  return; 
}

sub get_usrdata {
  my ($self, $usrname) = @_;
  my $e = OpenILS::Utils::CStoreEditor->new;
  my $query = {
    select => { au => ['id','home_ou'] },
    from   => 'au',
    where  => { usrname => $usrname }
  };
  my @result = $e->json_query($query);
  if (@result) {
    # This is admittedly ridiculous, but it works.
    my $usr_id = $result[0][0]->{id};
    my $home_ou = $result[0][0]->{home_ou};
    my $usrdata = { usr_id => $usr_id, home_ou => $home_ou };
    return $usrdata;
  } else {
    $logger->error("no usrdata found for $usrname");
    push @fail, { error => "INVALID_LOGIN: username = $usr, password = $pwd" };
    return;
  }
}

sub check_perms {
  my ($self, $usr_id, $home_ou) = @_;
  my $apputils = OpenILS::Application::AppUtils;
  my $p = $apputils->check_perms($usr_id, $home_ou, 'FLAG_USER_AS_DELETED');
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
  my ($self, $msgs) = @_;
  my $cgi = CGI->new;
  print $cgi->header,
        $cgi->start_html( -title => 'Sitka Patron Deletions - Login',
                          -style => { -src => "style.css" },
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

# The following is from OpenILS::WWW::Proxy by way of dbs's Evergreen development tutorial
sub oils_login {
    my( $username, $password, $type ) = @_;

    $type |= "staff";
    my $nametype = 'username';
    $nametype = 'barcode' if ($username =~ /^\d+$/o);

    my $seed = OpenSRF::AppSession
        ->create("open-ils.auth")
        ->request( 'open-ils.auth.authenticate.init', $username )
        ->gather(1);

    return undef unless $seed;

    my $response = OpenSRF::AppSession
        ->create("open-ils.auth")
        ->request( 'open-ils.auth.authenticate.complete', {
        $nametype => $username,
            password => md5_hex($seed . md5_hex($password)),
            type => $type
        })
        ->gather(1);

    return undef unless $response;

    return $response->{payload}->{authtoken};
}
1; # perl is stupid.
