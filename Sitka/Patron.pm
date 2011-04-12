#!/usr/bin/perl
package Sitka::Patron;
#use Sitka::DB;
use OpenSRF::System;
use OpenILS::Utils::CStoreEditor;

OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml');

sub new {
  my $class = shift;
  my $barcode = shift;
  my $ou = shift;
  my $self = {};
  bless $self, $class;
  bless $self;
  $self->{barcode}     = $barcode;
  $self->{ou}          = $ou;
  $self->{usr_id}      = 0;
  $self->{card_id}     = 0;
  $self->{givenname}   = undef;
  $self->{familyname}  = undef;
  $self->{circs}       = 0;
  $self->{holds}       = 0;
  $self->{fines}       = 0;
  $self->{msgs}        = ();
  return $self;
}

# get patron data from DB
sub retrieve {
  my ($self, $authtoken, $barcode) = shift;
  my $usr = OpenSRF::AppSession
    ->create('open-ils.actor')
    ->request( 'open-ils.actor.user.fleshed.retrieve_by_barcode', $authtoken, $barcode )
    ->gather(1);
  my $e = OpenILS::Utils::CStoreEditor->new;
  my $query = { 
    select => { ac => ['id'] }, 
    from => 'ac', 
    where => { usr => $usr->id, barcode => $barcode }
  };
  my $card = $e->json_query($query);
  if ($usr) {
    $self->usr_id($usr->id);
    $self->card_id($card->id);
    $self->givenname($usr->first_given_name);
    $self->familyname($usr->family_name);
    return $self;
  } else {
    $self->msgs('FAIL_NOT_FOUND');
    return;
  }
}

# check for active circs and holds
sub check_activity {
  my $self = shift;
  # TODO: use real OpenSRF calls instead of json_query
  my $e = OpenILS::Utils::CStoreEditor->new;
  my %checks = (
    circs => {
      select => { circ => ['id'] },
      from => 'circ',
      where => {
        usr => $self->usr_id,
        xact_finish => undef,
        checkin_time => undef
      }
    },
    holds => {
      select => ahr => ['id'],
      from => 'ahr',
      where => {
        usr => $self->usr_id,
        cancel_time => undef,
        fulfillment_time => undef,
        checkin_time => undef
      }
    }
  );
  foreach my $check (keys (%checks)) {
    my $query = $checks{$check};
    my $result = $e->json_query($query);
    my $check_count = scalar @$result;
    if ($check_count > 0) {
      $self->{$check} = $check_count;
      $self->msgs('FAIL_ACTIVE_XACTS') unless ( grep {'FAIL_ACTIVE_XACTS' eq $_} $self->{msgs} );
    }
  }
}

sub check_fines {
  my $self = shift;
  my $fines = OpenSRF::AppSession
    ->create('open-ils.storage')
    ->request( 'open-ils.storage.actor.user.total_owed', $self->usr_id )
    ->gather(1);
  if ($fines > 0) {
    $self->{fines} = $fines;
    $self->msgs('FAIL_HAS_FINES');
  }
}

# is the barcode we've been given the patron's primary card?
sub check_primary_card {
  my $self = shift;
  my $e = OpenILS::Utils::CStoreEditor->new;
  my $query = {
    select => { ac => ['barcode'] },
    from => 'ac',
    join => {
      au => {
        field => 'card',
        fkey => 'id'
      }
    },
    where => {
      '+ac' {
        'usr' => $self->usr_id
      }
    }
  };
  my $primary_card = $e->json_query($query);
  $self->msgs('FAIL_PRIMARY_CARD') if ($primary_card eq $self->{barcode});
  return;
}

# delete a patron and the card with the given barcode
# (other cards belonging to this user will not be affected)
sub delete_patron {
  my ($self, $authtoken) = shift;
  my $usr_rows_updated = OpenSRF::AppSession
    ->create('open-ils.actor')
    ->request('open-ils.actor.user.flag_as_deleted', $authtoken, $self->{usr_id})
    ->gather(1);
  $self->msgs('USER_NOT_DELETED') unless ($usr_rows_updated);
  my $card_rows_deleted = $self->delete_card;
  return $usr_rows_updated;
}

sub delete_card {
  my ($self, $authtoken) = shift;
  my $usr_rows_updated = OpenSRF::AppSession
    ->create('open-ils.actor')
    ->request('open-ils.actor.user.delete_card', $authtoken, $self->{card_id})
    ->gather(1);
  $self->msgs('CARD_NOT_DELETED') unless ($card_rows_deleted);
  return $card_rows_deleted;
}

sub barcode {
  my $self = shift;
  if (@_) { $self->{barcode} = shift; }
  return $self->{barcode};
}

sub ou {
  my $self = shift;
  if (@_) { $self->{ou} = shift; }
  return $self->{ou};
}

sub usr_id {
  my $self = shift;
  if (@_) { $self->{usr_id} = shift; }
  return $self->{usr_id};
}

sub card_id {
  my $self = shift;
  if (@_) { $self->{card_id} = shift; }
  return $self->{card_id};
}

sub givenname {
  my $self = shift;
  if (@_) { $self->{givenname} = shift; }
  return $self->{givenname};
}

sub familyname {
  my $self = shift;
  if (@_) { $self->{familyname} = shift; }
  return $self->{familyname};
}

sub circs {
  my $self = shift;
  if (@_) { $self->{circs} = shift; }
  return $self->{circs};
}

sub holds {
  my $self = shift;
  if (@_) { $self->{holds} = shift; }
  return $self->{holds};
}

sub fines {
  my $self = shift;
  if (@_) { $self->{fines} = shift; }
  return $self->{fines};
}

sub msgs {
  my $self = shift;
  if (@_) { push @{$self->{msgs}}, @_; }
  return $self->{msgs};
}

1; # perl is stupid.
