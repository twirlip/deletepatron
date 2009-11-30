#!/usr/bin/perl
package Sitka::DB;
use DBI;
use OpenSRF::System;
use OpenSRF::Utils::SettingsClient;

sub connect {
  my $self = {};
  bless $self;
  # get database connection info from fm_IDL.xml
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml'); 
  $settings  = OpenSRF::Utils::SettingsClient->new;
  $db_driver = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'driver');
  $db_host   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'host');
  $db_name   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'db');
  $db_user   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'user');
  $db_pw     = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'pw');
  $db_port   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'port');

  # database connection
  $dsn = "dbi:$db_driver:host=$db_host;dbname=$db_name;port=$db_port";
  $dbh = DBI->connect($dsn,$db_user,$db_pw);
  $dbh->do("BEGIN;");
  $self->{dbh} = $dbh;
  return $self;
}

# retrieve a single row from the database
sub lookup {
  my $self = shift;
  my $sql = shift;
  my @params = @_;
  my $result = $self->{dbh}->selectrow_hashref($sql, undef, @params);
  return $result;
}

sub do {
  my $self = shift;
  my $sql = shift;
  my @params = @_;
  my $rows_affected = $self->{dbh}->do($sql, {}, @params);
  return $rows_affected;
}

sub commit {
  my $self = shift;
  $self->{dbh}->do('COMMIT');
}

1; # perl is stupid.
