#!/usr/bin/perl
package Sitka::DB;
use DBI;
use OpenSRF::System;
use OpenSRF::Utils::SettingsClient;

sub new {
# get database connection info from fm_IDL.xml
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');
  my $settings  = OpenSRF::Utils::SettingsClient->new;
  my $db_driver = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'driver');
  my $db_host   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'host');
  my $db_name   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'db');
  my $db_user   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'user');
  my $db_pw     = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'pw');

  # database connection
  my $dsn = "dbi:$db_driver:host=$db_host;dbname=$db_name";
  $dbh = DBI->connect($dsn,$db_user,$db_pw);
  $dbh->do("BEGIN;") or die "Could not begin database transaction $dsn"; 
  return $dbh;
}

sub lookup {
  my $sql = shift @_;
  my $sth = $dbh->prepare($sql);
  $sth->execute(@_);
  my @result = $sth->fetchrow_array();
  $sth->finish;
  return @result;
}

1; # perl is stupid.
